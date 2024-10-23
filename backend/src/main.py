from backend.src.utils import *
from backend.src.dissertation_types import QueryRequest, QueryRequestThesis
from backend.src.configs import *
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn
import re
import asyncio

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

@app.post("/api/dissertation_analysis")
async def dissertation(request: QueryRequestThesis):
    degree_of_student = await extract_degree(request.thesis)
    name_of_author = await extract_name(request.thesis)
    topic = await extract_topic(request.thesis)
    summary_of_thesis = await summarize(request.thesis, topic, request.rubric)
    dissertation_system_prompt ="""You are an impartial academic evaluator - an expert in analyzing the summarized dissertation provided to you. 
Your task is to assess the quality of the provided summarized dissertation in relation to specific evaluation criteria. 
You will receive both the summarized dissertation and the criteria to analyze how effectively the dissertation addresses the research topic."""

    evaluation_results = {}
    total_score = 0

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
        
        # Generate the response using the utility function
        full_text_dict = await invoke_llm(
            system_prompt=dissertation_system_prompt,
            user_prompt=dissertation_user_prompt,
            ollama_model='command-r'
        )

        analyzed_dissertation = full_text_dict["answer"]
        print("###########################################Analysis Started##################################################")
        print(analyzed_dissertation)
        print("###########################################Analysis Finished##################################################")

        graded_response = await scoring_agent(analyzed_dissertation, criterion, explanation['score_explanation'], explanation['criteria_explanation'])

        print("###########################################Scoring Started##################################################")
        print(graded_response)
        print("###########################################Scoring Finished##################################################")

        # Extract score using regex with case-insensitivity
        pattern = r"spanda_score\s*:\s*(?:\*{1,2}\s*)?(\d+(?:\.\d+)?)\s*(?:\*{1,2})?"
        match = re.search(pattern, graded_response, re.IGNORECASE)

        # Create dictionary for this criterion's results
        criterion_result = {}
        criterion_result['feedback'] = analyzed_dissertation
        if match:
            score = float(match.group(1))
            criterion_result['score'] = score
            total_score += score
            print(f"Score for criterion '{criterion}': {score}")
        else:
            criterion_result['score'] = 0
            print(f"Score for criterion '{criterion}' not found.")
        # Add this criterion's results to the main dictionary
        evaluation_results[criterion] = criterion_result

    # Final response with structured feedback and total score
    response = {
        "criteria_evaluations": evaluation_results,
        "total_score": total_score,
        "name": name_of_author,
        "degree": degree_of_student,
        "topic": topic
    }
    
    return response


def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)

if __name__ == "__main__":
    main()