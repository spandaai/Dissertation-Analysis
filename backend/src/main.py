from backend.src.utils import *
from backend.src.dissertation_types import QueryRequestThesisAndRubric, ImageRequest, QueryRequestThesis
from backend.src.configs import *
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn
import re
from PIL import Image
import base64
from io import BytesIO


# Create FastAPI app instance
app = FastAPI(
    title="Dissertation Analysis API",
    description="API for analyzing dissertations",
    version="1.0.0"
)


# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, but you can specify a list of domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def read_root():
    return {"message": "Hello! This is the Dissertation Analysis! Dissertation Analysis app is running!"}


@app.post("/analyze-image/")
async def analyze_image(request: ImageRequest):
    image_agent_user_prompt = """
    Provide a detailed factual summary of each image.
    Identify all visible objects, elements, and features of the image.
    Describe the overall scene, composition, and setting depicted. 
    Avoid making inferences or interpretations beyond what can be directly observed.
    Present the summary in a clear and organized manner.
    """

    # Resize the image while maintaining aspect ratio
    image = Image.open(BytesIO(base64.b64decode(request.image_data)))
    max_size = 512
    width, height = image.size
    if max(width, height) > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        image = image.resize((new_width, new_height), resample=Image.BILINEAR)

    # Convert the resized image back to base64
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    resized_image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Call the generate_from_image function to get the analysis
    image_analyzed = await generate_from_image(resized_image_data, image_agent_user_prompt)

    # Return the analysis result
    return {"image_analysis": image_analyzed['response']}


@app.post("/api/pre_analyze")
async def pre_analysis(request: QueryRequestThesis):
    # Process non-streaming operations first
    degree_of_student = await extract_degree(request.thesis)
    name_of_author = await extract_name(request.thesis)
    topic = await extract_topic(request.thesis)
    summary_of_thesis = await summarize(request.thesis, topic)

    response = {
        "degree": degree_of_student,
        "name": name_of_author,
        "topic": topic,
        "pre_analyzed_summary": summary_of_thesis
    }
    
    return response


@app.websocket("/ws/dissertation_analysis")
async def websocket_dissertation(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Receive the initial data
        data = await websocket.receive_json()
        request = QueryRequestThesisAndRubric(**data)
        degree_of_student = request.pre_analysis.degree
        name_of_author = request.pre_analysis.name
        topic = request.pre_analysis.topic
        summary_of_thesis = request.pre_analysis.pre_analyzed_summary
        # Send initial metadata
        await websocket.send_json({
            "type": "metadata",
            "data": {
                "name": name_of_author,
                "degree": degree_of_student,
                "topic": topic
            }
        })

        dissertation_system_prompt = """You are an impartial academic evaluator - an expert in analyzing the summarized dissertation provided to you. 
Your task is to assess the quality of the provided summarized dissertation in relation to specific evaluation criteria. 
You will receive both the summarized dissertation and the criteria to analyze how effectively the dissertation addresses the research topic."""

        evaluation_results = {}
        total_score = 0

        # Process each criterion
        for criterion, explanation in request.rubric.items():
            dissertation_user_prompt = f"""
# Input Materials
## Dissertation Text
{summary_of_thesis}

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
                feedback_from_user = await feedback_generation(request.feedback)
                dissertation_user_prompt = dissertation_user_prompt + '\n' + "IMPORTANT: "+ feedback_from_user
            # Send criterion start marker
            await websocket.send_json({
                "type": "criterion_start",
                "data": {"criterion": criterion}
            })

            # Stream the analysis
            analysis_chunks = []
            async for chunk in stream_llm(
                system_prompt=dissertation_system_prompt,
                user_prompt=dissertation_user_prompt,
                ollama_model='llama3.1'
            ):
                analysis_chunks.append(chunk)
                await websocket.send_json({
                    "type": "analysis_chunk",
                    "data": {
                        "criterion": criterion,
                        "chunk": chunk
                    }
                })

            # Combine chunks for scoring
            analyzed_dissertation = "".join(analysis_chunks)
            
            # Get the score (non-streaming)
            graded_response = await scoring_agent(
                analyzed_dissertation, 
                criterion, 
                explanation['score_explanation'], 
                explanation['criteria_explanation']
            )

            # Extract score
            pattern = r"spanda_score\s*:\s*(?:\*{1,2}\s*)?(\d+(?:\.\d+)?)\s*(?:\*{1,2})?"
            match = re.search(pattern, graded_response, re.IGNORECASE)
            
            score = float(match.group(1)) if match else 0
            total_score += score

            # Send criterion completion
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
        print(evaluation_results)
        # Send final results
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
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)}
        })
    finally:
        await websocket.close()


def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)

if __name__ == "__main__":
    main()