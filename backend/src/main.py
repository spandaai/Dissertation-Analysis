from backend.src.utils import invoke_llm
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
    return {"message": "Hello! This is the Grading Assistant! Grading Assistant is running!"}

@app.post("/api/dissertation_analysis")
async def dissertation(request: QueryRequestThesis):
    dissertation_system_prompt ="""You are an impartial academic evaluator - an expert in analyzing the summarized dissertation provided to you. 
Your task is to assess the quality of the provided summarized dissertation in relation to specific evaluation criteria. 
You will receive both the summarized dissertation and the criteria to analyze how effectively the dissertation addresses the research topic."""


    overall_feedback = ""
    total_score = 0

    # Iterate over each criterion in the rubric dictionary
    for criterion, explanation in request.rubric.items():
        dissertation_user_prompt = f"""
Summarized Dissertation: 
    <START OF SUMMARIZED DISSERTATION>
        {request.thesis}
    <END OF SUMMARIZED DISSERTATION>

Evaluation Criterion: 
    <START CRITERION>
        {criterion} - {explanation}
    <END CRITERION>

Please evaluate the summarized Dissertation given on the criteria - {criterion} according to the rubric provided. Provide the evaluation in the following format -
    Justification: [Provide your detailed evaluation for the criterion '{criterion}' ensuring technical depth, rigorous critique, and full justification. Include specific examples from the dissertation to support your evaluation.]
    spanda_score = <score(out of 5)> - it is extremely important for the score to be in this exact format.
            """
        
        # Generate the response using the utility function
        full_text_dict = invoke_llm(
            system_prompt=dissertation_system_prompt,
            user_prompt=dissertation_user_prompt
        )

        graded_response = full_text_dict["answer"]


        # Extract score using regex
        pattern = r"spanda_score\s*=\s*(\d+)"
        match = re.search(pattern, graded_response)

        if match:
            score = int(match.group(1))
            total_score += score  # Add score to the total
            print(f"Score for criterion '{criterion}': {score}")
        else:
            score = None
            print(f"Score for criterion '{criterion}' not found.")

        # Append feedback for this criterion to the overall feedback
        overall_feedback += f"\nEvaluation for {criterion}:\n{graded_response}\n\n\n"
        print(overall_feedback)
    # Final response with aggregated feedback and score
    response = {
        "justification": overall_feedback.strip(),
        "score": total_score
    }
    
    return response



@app.post("/api/summarize")
async def summarize(request: QueryRequest):
    summarize_system_prompt = (
        """
You are an expert summarizer with a focus on brevity and clarity. Your goal is to produce a clear, concise summary that captures only the most important details, names, dates, and key points. 
Ensure that the core meaning and critical nuances are preserved while significantly reducing the length of the text. Avoid redundant phrases or introductory language like 'this is a summary.'
        """
    )

    summarize_user_prompt = (
            f"""
Text: 
<START OF TEXT>

    {request.query}

<END OF TEXT>

Summarize the above text in a clear and concise manner while ensuring that all important details, facts, and key points are preserved. 
Avoid omitting any crucial information, and maintain the original meaning and intent of the content. But reduce the length of the text significantly. 
The main goal is to create a significantly smaller version of the text.
            """
        )
    
    # Generate the response using the utility function
    full_text_dict = invoke_llm(
        system_prompt=summarize_system_prompt,
        user_prompt=summarize_user_prompt
    )

    summarized_text = full_text_dict["answer"]
    
    print(summarized_text)
    response = {
        "summarized_text": summarized_text
    }
    
    return response

# Run the app using uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
