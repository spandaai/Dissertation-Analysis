"""
Dissertation Analysis WebSocket Handler and Analysis Algorithm

This module implements a WebSocket-based real-time dissertation analysis system that:
- Processes dissertation evaluation requests using a streaming approach
- Handles communication between the frontend and the LLM-based analysis backend
- Implements a criterion-by-criterion evaluation process with real-time updates

Technical Components:
- WebSocket for real-time bidirectional communication
- FastAPI for WebSocket server implementation
- Custom LLM streaming integration for analysis
- Cancellation token pattern for process control
- Regex-based score extraction from LLM responses

Core Functionality:
1. Accepts dissertation text, rubric, and metadata via WebSocket
2. Streams analysis progress and results back to the client
3. Processes each rubric criterion individually:
   - Generates criterion-specific prompts
   - Streams analysis chunks in real-time
   - Extracts and validates scores
   - Handles expert feedback integration
4. Provides comprehensive error handling and WebSocket connection management
5. Calculates and returns total scores and detailed criterion evaluations

The system supports:
- Graceful cancellation of in-progress analysis
- Safe WebSocket message delivery
- Structured response formats for different message types (metadata, analysis, scores)
- Expert feedback incorporation into the analysis process
"""

import re
import logging
from dissertation_analysis.common.types import CancellationToken, QueryRequestThesisAndRubric
from dissertation_analysis.common.configs import ModelType
from dissertation_analysis.domain.business_logic import scoring_agent
from typing import Dict, Any
from dissertation_analysis.platform.service_client import stream_llm

from fastapi import WebSocket, WebSocketDisconnect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DissertationAnalyzer:
    def __init__(self):
        self.cancellation_token = CancellationToken()
        self.is_connection_closed = False

    async def handle_disconnect(self):
        """Handle WebSocket disconnection"""
        self.cancellation_token.cancel()
        self.mark_connection_closed()
        print("WebSocket disconnected, cancelling LLM generation")

    def mark_connection_closed(self):
        """Mark the WebSocket connection as closed"""
        self.cancellation_token.mark_closed()
        self.is_connection_closed = True

    async def safe_send(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """Safely send a message through the WebSocket"""
        if self.cancellation_token.is_cancelled or self.is_connection_closed:
            return False
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            self.mark_connection_closed()
            return False

    async def process_criterion(self, 
                              websocket: WebSocket, 
                              criterion: str, 
                              explanation: Dict[str, str], 
                              context: Dict[str, str],
                              feedback: str = None) -> tuple[float, str]:
        """Process a single criterion and return its score and analysis"""
        
        # Send criterion start marker
        if not await self.safe_send(websocket, {
            "type": "criterion_start",
            "data": {"criterion": criterion}
        }):
            return 0, ""

        dissertation_user_prompt = self._build_criterion_prompt(
            criterion, 
            explanation, 
            context,
            feedback
        )

        # Stream the analysis
        analysis_chunks = []
        try:
            async for chunk in stream_llm(
                system_prompt=self.DISSERTATION_SYSTEM_PROMPT,
                user_prompt=dissertation_user_prompt,
                model_type=ModelType.ANALYSIS,
                cancellation_token=self.cancellation_token
            ):
                if self.cancellation_token.is_cancelled:
                    return 0, ""
                    
                analysis_chunks.append(chunk)
                if not await self.safe_send(websocket, {
                    "type": "analysis_chunk",
                    "data": {
                        "criterion": criterion,
                        "chunk": chunk
                    }
                }):
                    return 0, ""

            analyzed_dissertation = "".join(analysis_chunks)
            
            # Get the score
            score = await self._calculate_score(
                analyzed_dissertation, 
                criterion, 
                explanation,
                feedback
            )

            # Send criterion completion
            if not await self.safe_send(websocket, {
                "type": "criterion_complete",
                "data": {
                    "criterion": criterion,
                    "score": score,
                    "full_analysis": analyzed_dissertation
                }
            }):
                return 0, ""

            return score, analyzed_dissertation

        except Exception as e:
            print(f"Error processing criterion {criterion}: {str(e)}")
            if not self.is_connection_closed:
                await self.safe_send(websocket, {
                    "type": "error",
                    "data": {
                        "message": f"Error processing criterion {criterion}: {str(e)}",
                        "criterion": criterion
                    }
                })
            return 0, ""

    async def process_dissertation(self, websocket: WebSocket, request: QueryRequestThesisAndRubric):
        """Process the entire dissertation analysis"""
        context = {
            "name": request.pre_analysis.name,
            "degree": request.pre_analysis.degree,
            "topic": request.pre_analysis.topic,
            "summary": request.pre_analysis.pre_analyzed_summary
        }

        # Send initial metadata
        if not await self.safe_send(websocket, {
            "type": "metadata",
            "data": {
                "name": context["name"],
                "degree": context["degree"],
                "topic": context["topic"]
            }
        }):
            return

        evaluation_results = {}
        total_score = 0

        # Process each criterion
        for criterion, explanation in request.rubric.items():
            if self.cancellation_token.is_cancelled:
                break

            score, analysis = await self.process_criterion(
                websocket, 
                criterion, 
                explanation, 
                context,
                request.feedback
            )
            
            total_score += score
            evaluation_results[criterion] = {
                "feedback": analysis,
                "score": score
            }

        if not self.cancellation_token.is_cancelled and not self.is_connection_closed:
            await self.safe_send(websocket, {
                "type": "complete",
                "data": {
                    "criteria_evaluations": evaluation_results,
                    "total_score": total_score,
                    **context
                }
            })

    def _build_criterion_prompt(self, 
                              criterion: str, 
                              explanation: Dict[str, str], 
                              context: Dict[str, str],
                              feedback: str = None) -> str:
        """Build the prompt for criterion evaluation"""
        prompt = f"""
# Input Materials
## Dissertation Text
{context['summary']}

## Evaluation Context
- Author: {context['name']}
- Academic Field: {context['degree']}

## Assessment Criterion and its explanation
### {criterion}:
#### Explanation: {explanation['criteria_explanation']}

{explanation['criteria_output']}

Please make sure that you critique the work heavily, including all improvements that can be made.

DO NOT SCORE THE DISSERTATION, YOU ARE TO PROVIDE ONLY DETAILED ANALYSIS, AND NO SCORES ASSOCIATED WITH IT.
"""
        if feedback:
            prompt += '\nIMPORTANT(The following feedback was provided by an expert. Consider the feedback properly, and ensure your evaluation follows this feedback): ' + feedback
        
        return prompt

    async def _calculate_score(self, 
                             analysis: str, 
                             criterion: str, 
                             explanation: Dict[str, str],
                             feedback: str = None) -> float:
        """Calculate the score for a criterion based on the analysis"""
        graded_response = await scoring_agent(
            analysis, 
            criterion, 
            explanation['score_explanation'], 
            explanation['criteria_explanation'],
            feedback
        )

        # Extract score using regex
        pattern = r"spanda_score\s*:\s*(?:\*{1,2}\s*)?(\d+(?:\.\d+)?)\s*(?:\*{1,2})?"
        match = re.search(pattern, graded_response, re.IGNORECASE)
        return float(match.group(1)) if match else 0

    DISSERTATION_SYSTEM_PROMPT = """You are an impartial academic evaluator - an expert in analyzing the summarized dissertation provided to you. 
Your task is to assess the quality of the provided summarized dissertation in relation to specific evaluation criteria. 
You will receive both the summarized dissertation and the criteria to analyze how effectively the dissertation addresses the research topic."""



async def safe_send(websocket: WebSocket, cancellation_token: CancellationToken, message: dict) -> bool:
    """Safely send a message through the WebSocket if it's still open"""
    if not cancellation_token.ws_closed:
        try:
            await websocket.send_json(message)
            return True
        except RuntimeError as e:
            print(f"WebSocket send failed: {str(e)}")
            cancellation_token.mark_closed()
            return False
    return False


async def process_request(websocket: WebSocket, request: QueryRequestThesisAndRubric, cancellation_token: CancellationToken):
    """
    Process the dissertation analysis request and stream results via the WebSocket.
    """
    try:
        # Send initial metadata to the frontend
        degree_of_student = request.pre_analysis.degree
        name_of_author = request.pre_analysis.name
        topic = request.pre_analysis.topic

        await websocket.send_json({
            "type": "metadata",
            "data": {
                "name": name_of_author,
                "degree": degree_of_student,
                "topic": topic
            }
        })

        # Dissertation evaluation process
        dissertation_system_prompt = """You are an impartial academic evaluator - an expert in analyzing the summarized dissertation provided to you. 
Your task is to assess the quality of the provided summarized dissertation in relation to specific evaluation criteria."""

        evaluation_results = {}
        total_score = 0

        # Process each rubric criterion
        for criterion, explanation in request.rubric.items():
            if cancellation_token.is_cancelled:
                logger.info(f"Processing canceled for criterion: {criterion}")
                break

            # Build the user prompt for this criterion
            dissertation_user_prompt = f"""
# Input Materials
## Dissertation Text
{request.pre_analysis.pre_analyzed_summary}

## Evaluation Context
- Author: {name_of_author}
- Academic Field: {degree_of_student}

## Assessment Criterion and its explanation
### {criterion}:
#### Explanation: {explanation['criteria_explanation']}

{explanation['criteria_output']}

Please make sure that you critique the work heavily, including all improvements that can be made.

DO NOT SCORE THE DISSERTATION, YOU ARE TO PROVIDE ONLY DETAILED ANALYSIS, AND NO SCORES ASSOCIATED WITH IT.
"""
            if request.feedback:
                dissertation_user_prompt += f'\nIMPORTANT(The following feedback was provided by an expert. Consider the feedback properly, and ensure your evaluation follows this feedback): {request.feedback}'

            # Notify the frontend about the start of the criterion evaluation
            await websocket.send_json({
                "type": "criterion_start",
                "data": {"criterion": criterion}
            })

            # Stream analysis results to the client
            analysis_chunks = []
            try:
                async for chunk in stream_llm(
                    system_prompt=dissertation_system_prompt,
                    user_prompt=dissertation_user_prompt,
                    model_type=ModelType.ANALYSIS,
                    cancellation_token=cancellation_token
                ):
                    if cancellation_token.is_cancelled:
                        logger.info(f"Streaming canceled for criterion: {criterion}")
                        break

                    analysis_chunks.append(chunk)
                    await websocket.send_json({
                        "type": "analysis_chunk",
                        "data": {
                            "criterion": criterion,
                            "chunk": chunk
                        }
                    })

                if not cancellation_token.is_cancelled:
                    analyzed_dissertation = "".join(analysis_chunks)

                    # Perform scoring
                    graded_response = await scoring_agent(
                        analyzed_dissertation, 
                        criterion, 
                        explanation['score_explanation'], 
                        explanation['criteria_explanation'],
                        request.feedback
                    )

                    # Extract score using regex
                    pattern = r"spanda_score\s*:\s*(?:\*{1,2}\s*)?(\d+(?:\.\d+)?)\s*(?:\*{1,2})?"
                    match = re.search(pattern, graded_response, re.IGNORECASE)
                    score = float(match.group(1)) if match else 0
                    total_score += score

                    # Send criterion completion details
                    await websocket.send_json({
                        "type": "criterion_complete",
                        "data": {
                            "criterion": criterion,
                            "score": score,
                            "full_analysis": analyzed_dissertation
                        }
                    })

                    evaluation_results[criterion] = {
                        "feedback": analyzed_dissertation,
                        "score": score
                    }

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected during analysis of criterion: {criterion}")
                cancellation_token.mark_closed()
                break
            except Exception as e:
                logger.error(f"Error processing criterion {criterion}: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "message": f"Error processing criterion {criterion}: {str(e)}",
                        "criterion": criterion
                    }
                })
                break

        # Send final evaluation results
        if not cancellation_token.is_cancelled:
            await websocket.send_json({
                "type": "complete",
                "data": {
                    "criteria_evaluations": evaluation_results,
                    "total_score": total_score,
                    "name": name_of_author,
                    "degree": degree_of_student,
                    "topic": topic
                }
            })

    except Exception as e:
        logger.error(f"Error in process_request: {e}")
        if not cancellation_token.ws_closed:
            await websocket.send_json({"type": "error", "data": {"message": str(e)}})
