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

from dissertation_analysis.domain.FunctionalBlocks.AnalysisAlgorithms.types import CancellationToken, QueryRequestThesisAndRubric

from dissertation_analysis.platform.service_client import stream_llm, invoke_llm
from dissertation_analysis.common.configs import ModelType

from fastapi import WebSocket
from typing import Dict, Any

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




async def scoring_agent(analysis, criteria, score_guidelines, criteria_guidelines, feedback):
    scoring_agent_system_prompt = """You are a precise scoring agent that evaluates one dissertation criterion at a time. 
    Review the provided criterion analysis, match it to the scoring guidelines, and assign a score from 0 to 5, without justification, solely use the analysis for your justification. 
    Evaluate only the assigned criterion, using only the given analysis, and follow the guidelines exactly. 
    Do not consider external factors, make assumptions, or deviate from objective standards."""

    scoring_agent_user_prompt = f"""# Provide a score for the following analysis done:

-Analysis: {analysis}

-Explanation of {criteria}: {criteria_guidelines}

-Guidelines of scoring for {criteria}: {score_guidelines}

Your score will only be for the following criterion: {criteria}. Provide ONLY the score based on the analysis that has been done. Be very critical while providing the score.

IMPORTANT(The following feedback was provided by an expert. Consider the feedback properly, and ensure your evaluation follows this feedback): {feedback}

Required output format. It is extremely important for the score to be displayed in this exact format with no formatting and whitespaces:
spanda_score: <score (out of 5)>"""
        
    # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=scoring_agent_system_prompt,
        user_prompt=scoring_agent_user_prompt,
        model_type=ModelType.SCORING
    )

    score_for_criteria = full_text_dict["answer"]
    
    return score_for_criteria 
