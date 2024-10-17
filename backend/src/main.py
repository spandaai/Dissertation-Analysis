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
    return {"message": "Hello! This is the Dissertation Analysis! Dissertation Analysis app is running!"}

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
Dissertation: 
    <START OF DISSERTATION>
        {request.thesis}
    <END OF DISSERTATION>

Evaluation Criterion: 
    <START CRITERION>
        {criterion} - {explanation}
    <END CRITERION>

Please evaluate the Dissertation based on the given criterion: {criterion}. Make sure to follow the rubric closely.

Guidelines for Evaluation:
1. Provide a comprehensive analysis by breaking down the evaluation into different aspects relevant to the criterion. Consider factors such as depth of research, clarity of argument, originality, quality of evidence, coherence, and overall impact.
2. Justify the evaluation with specific examples or sections from the dissertation where the criterion is met or lacking.
3. If the dissertation has any notable strengths or weaknesses regarding the criterion, mention them and explain their significance.
4. Make recommendations for improvement, if applicable.

It is extremely important for the score and justification to be in the following exact format (providing both a justification and spanda_score):
    - Justification: <Provide a detailed and structured evaluation for the criterion '{criterion}', including specific references and examples from the dissertation. Discuss strengths, weaknesses, and any nuances. >
    - spanda_score = <score (out of 5)> for {criterion}
"""

        
        # Generate the response using the utility function
        full_text_dict = await invoke_llm(
            system_prompt=dissertation_system_prompt,
            user_prompt=dissertation_user_prompt,
            ollama_model = 'llama3.1'
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
You are an expert summarizer specializing in academic dissertations. Your goal is to produce a clear, concise summary that captures the most important details, names, dates, key points, and arguments from the dissertation. 
While focusing on brevity and clarity, ensure that each relevant section and its significance is maintained, and critical nuances are preserved. Avoid unnecessary details and redundant phrases, while keeping the essential structure and flow of the original content.
Do not use introductory language like 'this is a summary' or 'here is my'—focus directly on the content.
    """
    )


    def chunk_text(text, chunk_size=1000):
        # Split the text into words
        words = text.split()
        # Generate chunks of the specified size
        for i in range(0, len(words), chunk_size):
            yield " ".join(words[i:i + chunk_size])

    # Chunk the input text
    chunks = list(chunk_text(request.query, chunk_size=1000))

    # Summarize each chunk and collect the results
    summarized_chunks = []
    for chunk in chunks:
        summarize_user_prompt = (
    f"""
Dissertation chunk (part of a larger document): 
    <START OF DISSERTATION CHUNK>
        {chunk}
    <END OF DISSERTATION CHUNK>

Produce an exhaustive summary of the above dissertation chunk. 
Ensure that all fact, detail, course-related information, title, key point, and argument is included. 
Note that this is just one section, and more chunks will be provided. Do not treat this as the complete dissertation.
    """
        )

        # Generate the response using the utility function
        full_text_dict = await invoke_llm(
            system_prompt=summarize_system_prompt,
            user_prompt=summarize_user_prompt,
            ollama_model = 'nemotron-mini'
        )

        summarized_chunk = full_text_dict["answer"]
        summarized_chunks.append(summarized_chunk)

    # Combine all summarized chunks into a final summary
    final_summary = " ".join(summarized_chunks)
    
    print(final_summary)
    response = {
        "summarized_text": final_summary
    }
    
    return response

def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)

if __name__ == "__main__":
    main()  # Call the main function if the script is run directly