import os
from dotenv import load_dotenv
from backend.src.utils import *

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")
verba_url = os.getenv("VERBA_URL")
ollama_model_for_summary = os.getenv("OLLAMA_MODEL_FOR_SUMMARY")
ollama_model_for_extraction = os.getenv("OLLAMA_MODEL_FOR_EXTRACTION")
ollama_model_for_analysis = os.getenv("OLLAMA_MODEL_FOR_ANALYSIS")


async def summarize_and_analyze_agent(thesis, topic):
    summarize_system_prompt = f"""
    You are an expert in summarizing academic dissertations, aiming to capture key details, names, dates, points, and arguments in a clear, brief summary. 
    Focus on each section's significance while preserving essential nuances. Avoid unnecessary details and introductory phrases.
    """
    chunks = chunk_text(thesis, chunk_size=1000)
    summarized_chunks = []
    for chunk in chunks:
        summarize_user_prompt = f'''
# Input Content
## Dissertation Segment
{chunk[0]}

## Context
Topic: {topic}

# Summarization Instructions
1. Create a concise summary that:
   - Captures essential arguments
   - Retains key facts and details
   - Maintains logical flow
   - Connects to overall topic: {topic}
   - Acknowledges this is part of a larger work

# Output Requirements
- Do not miss crucial details, but significantly reduced length and condensed information with no formatting.
- Maintain academic tone
- Do NOT guess. Just summarize whatever is mentioned in the dissertation chunk. Do not add anything to the dissertation chunk, just summarize.
- Provide ONLY the summarized text, no filler words or formatting. Avoid summarizing references. Keep the summarization very concise and condensed.
'''

        # Generate the response using the utility function
        try:
            full_text_dict = await invoke_llm(
                system_prompt=summarize_system_prompt,
                user_prompt=summarize_user_prompt,
                ollama_model=ollama_model_for_summary 
            )

            summarized_chunk = full_text_dict["answer"]
            print(summarized_chunk)
            summarized_chunks.append(summarized_chunk)

        except Exception as e:
            print(f"Error during LLM invocation: {e}")
            summarized_chunks.append("")  # Append an empty string if there's an error

    # Combine all summarized chunks into a final summary
    final_summary = " ".join(summarized_chunks).replace("\n", "")

    response = final_summary

    return response

async def extract_name_agent(dissertation):
    
    dissertation_first_pages = get_first_n_words(dissertation, 300)

    extract_name_system_prompt = """
    You are an academic expert tasked with identifying the author of a dissertation. Your job is to find the exact wording or phrase in the text that clearly indicates the author's name.
    Do not interpret, summarize, or infer—only locate and extract the exact name mentioned in the text. Respond with the precise name as it appears in the document.
    """

    extract_name_user_prompt = f"""
# Author Name Extraction
## Input
The text contains the first few pages of a dissertation:

[CHUNK STARTS]
{dissertation_first_pages}
[CHUNK ENDS]

## Instructions
- Extract the exact wording or phrase that clearly states the author's name
- Return ONLY the exact name as mentioned in the text
- Do not include any additional explanation or comments
- Only extract and send the name, nothing else.

## Output Format
Name should be returned exactly as written in the text. If there is no name available, please return exactly the following:
"no_name_found"
"""
        
        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_name_system_prompt,
        user_prompt=extract_name_user_prompt,
        ollama_model = ollama_model_for_extraction 
    )

    name = full_text_dict["answer"]
    print("THE NAME IS IS: " + name)
    # Final response with aggregated feedback and score
    
    return name 


async def extract_topic_agent(dissertation):
    
    dissertation_first_pages = get_first_n_words(dissertation, 300)

    extract_topic_system_prompt = """
You are an academic expert tasked with identifying the main topic of a dissertation. Your job is to find the exact wording or phrase in the text that clearly indicates the primary topic the student is working on.
Do not interpret, summarize, or infer—only locate and extract the exact topic mentioned in the text. Respond with the precise words or phrase that describe the topic.
"""

    # Prompt to extract main topic
    extract_topic_user_prompt = f"""
# Topic Extraction
## Input
The text contains the first few pages of a dissertation:

[CHUNK STARTS]
{dissertation_first_pages}
[CHUNK ENDS]

## Instructions
- Extract the exact wording or phrase that clearly states the main topic
- Return ONLY the exact topic as mentioned in the text
- Do not include any additional explanation or comments
- Only extract and send the topic, nothing else.

## Output Format
Topic should be returned exactly as written in the text. If there is no topic available, please return exactly the following:
"no_topic_found"
"""

        
        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_topic_system_prompt,
        user_prompt=extract_topic_user_prompt,
        ollama_model = ollama_model_for_extraction
    )

    topic = full_text_dict["answer"]
    print("THE TOPIC IS: " + topic)
    # Final response with aggregated feedback and score
    
    return topic 


async def extract_degree_agent(dissertation):
    
    dissertation_first_pages = get_first_n_words(dissertation, 300)

    extract_degree_system_prompt = """
You are an academic expert tasked with identifying the degree that the submitter is pursuing in a dissertation. Your job is to find the exact wording or phrase in the text that clearly indicates the degree being pursued by the student.
Do not interpret, summarize, or infer—only locate and extract the exact degree mentioned in the text. Respond with the precise words or phrase that describe the degree.
"""

    extract_degree_user_prompt = f"""
# Degree Information Extraction
## Input
The text contains the first few pages of a dissertation:

[CHUNK STARTS]
{dissertation_first_pages}
[CHUNK ENDS]

## Instructions
- Extract the exact wording or phrase that clearly states the degree being pursued
- Return ONLY the exact degree as mentioned in the text
- Do not include any additional explanation or comments
- Only extract and send the degree, nothing else.

# Output Format
Degree should be returned exactly as written in the text. If there is no degree available, please return exactly the following:
"no_degree_found"
"""

        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_degree_system_prompt,
        user_prompt=extract_degree_user_prompt,
        ollama_model = ollama_model_for_extraction
    )
    
    degree = full_text_dict["answer"]
    print("THE DEGREE IS: " + degree)
    
    return degree 

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
        ollama_model = ollama_model_for_analysis 
    )

    score_for_criteria = full_text_dict["answer"]
    
    return score_for_criteria 
