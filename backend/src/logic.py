from backend.Agents.text_agents import scoring_agent
from backend.InferenceEngine.inference_engines import stream_llm, ModelType, invoke_llm
from backend.src.types import QueryRequestThesisAndRubric

from fastapi import WebSocket, WebSocketDisconnect
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CancellationToken:
    def __init__(self):
        self.is_cancelled = False
        self.ws_closed = False

    def cancel(self):
        self.is_cancelled = True

    def mark_closed(self):
        self.ws_closed = True

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


async def process_request(request: QueryRequestThesisAndRubric):
    """
    Process the dissertation analysis request and return results.
    """
    try:
        # Check initial metadata to process request
        degree_of_student = request.pre_analysis.degree
        name_of_author = request.pre_analysis.name
        topic = request.pre_analysis.topic
    
    except Exception as e:
        logger.error(f"Error in process_request: {e}")

    # Dissertation evaluation process
    dissertation_system_prompt = """You are an impartial academic evaluator - an expert in analyzing the summarized dissertation provided to you. 
Your task is to assess the quality of the provided summarized dissertation in relation to specific evaluation criteria."""

    evaluation_results = {}
    total_score = 0

    # Process each rubric criterion
    for criterion, explanation in request.rubric.items():

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

        # Stream analysis results to the client
        try:
            analyzed_dissertation = await invoke_llm(
                    system_prompt=dissertation_system_prompt,
                    user_prompt=dissertation_user_prompt,
                    model_type=ModelType.ANALYSIS,
                )
            
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

            evaluation_results[criterion] = {
                "feedback": analyzed_dissertation['answer'],
                "score": score
            }

        except Exception as e:
            logger.error(f"Error processing criterion {criterion}: {str(e)}")
            break

    # Send final evaluation results

    return {
        "criteria_evaluations": evaluation_results,
        "total_score": total_score,
        "name": name_of_author,
        "degree": degree_of_student,
        "topic": topic
    }