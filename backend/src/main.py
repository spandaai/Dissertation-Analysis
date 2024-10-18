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
    degree_of_student = await extract_degree(request.thesis)
    summary_of_thesis = await summarize(request.thesis)
    dissertation_system_prompt ="""You are an impartial academic evaluator - an expert in analyzing the summarized dissertation provided to you. 
Your task is to assess the quality of the provided summarized dissertation in relation to specific evaluation criteria. 
You will receive both the summarized dissertation and the criteria to analyze how effectively the dissertation addresses the research topic."""

    evaluation_results = {}
    total_score = 0

    for criterion, explanation in request.rubric.items():
        dissertation_user_prompt = f"""
Dissertation: 
    <START OF DISSERTATION>
        {summary_of_thesis}
    <END OF DISSERTATION>

Evaluation Criterion: 
    <START CRITERION>
        {criterion} - {explanation}
    <END CRITERION>
The student is pursuing {degree_of_student}.

Please evaluate the Dissertation based on the exact given criterion: {criterion}. 
Do not divert from the criteria and its given rules. 
Make sure to give detailed analysis along with the final spanda_score only on the specific criteria mentioned.
It is important to mention specifics instead of generalized statements. Mention specific pieces which misallign or allign.

The most important part is for the spanda_score to be in the EXACT following format, without any change
    - spanda_score = <score (out of 5)> for {criterion}
"""
        
        # Generate the response using the utility function
        full_text_dict = await invoke_llm(
            system_prompt=dissertation_system_prompt,
            user_prompt=dissertation_user_prompt,
            ollama_model='llama3.1'
        )

        graded_response = full_text_dict["answer"]
        print(graded_response)
        # Extract score using regex
        # Extract score using regex with case-insensitivity
        pattern = r"spanda_score\s*=\s*(\d+)"
        match = re.search(pattern, graded_response, re.IGNORECASE)

        # Create dictionary for this criterion's results
        criterion_result = {}
        criterion_result['feedback'] = graded_response
        if match:
            score = int(match.group(1))
            criterion_result['score'] = score
            total_score += score
            print(f"Score for criterion '{criterion}': {score}")
        else:
            criterion_result['score'] = None
            print(f"Score for criterion '{criterion}' not found.")
        # Add this criterion's results to the main dictionary
        evaluation_results[criterion] = criterion_result

    # Final response with structured feedback and total score
    response = {
        "criteria_evaluations": evaluation_results,
        "total_score": total_score
    }
    
    return response

def chunk_text(text, chunk_size=1000):
    # Split the text into words
    words = text.split()
    # Generate chunks of the specified size
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])

async def summarize(thesis):
    summarize_system_prompt = """
    You are an expert in summarizing academic dissertations, aiming to capture key details, names, dates, points, and arguments in a clear, brief summary. 
    Focus on each section's significance while preserving essential nuances. Avoid unnecessary details and introductory phrases.
    """

    topic = await extract_topic(thesis)
    chunks = list(chunk_text(thesis, chunk_size=1000))

    summarized_chunks = []
    for chunk in chunks:
        summarize_user_prompt = f"""
    Dissertation chunk: 
    #####################################CHUNK START########################################
        {chunk}
    #####################################CHUNK END##########################################

    The topic for overall dissertation is : {topic}
    Summarize the above chunk concisely, including key facts, details and arguments while reducing the size greatly. Include the essence of the chunk. Treat this as part of a larger document.
        """


        # Generate the response using the utility function
        full_text_dict = await invoke_llm(
            system_prompt=summarize_system_prompt,
            user_prompt=summarize_user_prompt,
            ollama_model = 'qwen2.5'
        )

        summarized_chunk = full_text_dict["answer"]
        summarized_chunks.append(summarized_chunk)

    # Combine all summarized chunks into a final summary
    final_summary = " ".join(summarized_chunks)
    
    print(final_summary)
    response = final_summary

    return response

def get_first_100_words(text):
    # Split the text into words
    words = text.split()
    # Get the first 500 words
    first_100_words = words[:100]
    # Join them back into a string
    return " ".join(first_100_words)

async def extract_topic(dissertation):
    
    dissertation_first_pages = get_first_100_words(dissertation)

    extract_topic_system_prompt = """
You are an academic expert tasked with identifying the main topic of a dissertation. Your job is to find the exact wording or phrase in the text that clearly indicates the primary topic the student is working on.
Do not interpret, summarize, or infer—only locate and extract the exact topic mentioned in the text. Respond with the precise words or phrase that describe the topic.
"""

    extract_topic_user_prompt = f"""
Please identify the exact main topic from the following text. The text contains the first few pages of a dissertation:

[CHUNK STARTS]
    {dissertation_first_pages}
[CHUNK ENDS]

Extract the exact wording or phrase that clearly states the main topic of the dissertation. Respond ONLY with the exact topic mentioned in the text, without any additional explanation or comments.
"""

        
        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_topic_system_prompt,
        user_prompt=extract_topic_user_prompt,
        ollama_model = 'llama3.1'
    )

    topic = full_text_dict["answer"]
    print("THE TOPIC IS: " + topic)
    # Final response with aggregated feedback and score
    response = {
        "topic": topic,
    }
    
    return response   


async def extract_degree(dissertation):
    
    dissertation_first_pages = get_first_100_words(dissertation)

    extract_degree_system_prompt = """
You are an academic expert tasked with identifying the degree that the submitter is pursuing in a dissertation. Your job is to find the exact wording or phrase in the text that clearly indicates the degree being pursued by the student.
Do not interpret, summarize, or infer—only locate and extract the exact degree mentioned in the text. Respond with the precise words or phrase that describe the degree.
"""

    extract_degree_user_prompt = f"""
Please identify the exact degree that the submitter is pursuing from the following text. The text contains the first few pages of a dissertation:

[CHUNK STARTS]
    {dissertation_first_pages}
[CHUNK ENDS]

Extract the exact wording or phrase that clearly states the degree being pursued by the submitter. Respond ONLY with the exact degree mentioned in the text, without any additional explanation or comments.
"""

        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_degree_system_prompt,
        user_prompt=extract_degree_user_prompt,
        ollama_model = 'llama3.1'
    )

    degree = full_text_dict["answer"]
    print("THE DEGREE IS: " + degree)
    # Final response with aggregated feedback and score
    response = {
        "degree": degree,
    }
    
    return response   


def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)

if __name__ == "__main__":
    main()  # Call the main function if the script is run directly