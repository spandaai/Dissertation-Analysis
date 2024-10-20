from backend.src.utils import *
from backend.src.dissertation_types import QueryRequest, QueryRequestThesis
from backend.src.configs import *
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn
import re
from fastapi.middleware.cors import CORSMiddleware 

app = FastAPI()


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
### {criterion} :
#### Explanation: {explanation}

# Required Output Format and Instructions
   1. Clearly state understanding and scope of evaluation target with respect to {criterion}
   2. Connect evidence directly to criterion. Give a detailed analysis pointwise on the strengths and weaknesses of the dissertation when it comes to "{criterion}".
   3. Whatever weaknesses and strengths are mentioned, provide specific examples from the dissertation that justify those.
   4. Provide specific, actionable recommendations for improvements to the dissertation.
   5. Identify and address key concepts or technologies that can be used to solve the problem but may be missing. 
   6. Ensure feedback is precise, grounded, and directly useful for enhancing the content.
2. It is important to provide the final score this in this exact format, no changes in any of the characters or spaces.
spanda_score: <score (out of 5)> for {criterion}
"""
        
        # Generate the response using the utility function
        full_text_dict = await invoke_llm(
            system_prompt=dissertation_system_prompt,
            user_prompt=dissertation_user_prompt,
            ollama_model='llama3.1'
        )

        graded_response = full_text_dict["answer"]
        print("#################################################################################")
        print(graded_response)
        # Extract score using regex
        # Extract score using regex with case-insensitivity
        pattern = r"spanda_score\s*:\s*(?:\*{1,2}\s*)?(\d+(?:\.\d+)?)\s*(?:\*{1,2})?"
        match = re.search(pattern, graded_response, re.IGNORECASE)

        # Create dictionary for this criterion's results
        criterion_result = {}
        criterion_result['feedback'] = graded_response
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
    main()  # Call the main function if the script is run directly