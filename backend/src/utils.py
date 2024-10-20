import json
import httpx
import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")
ollama_model = os.getenv("OLLAMA_MODEL")
verba_url = os.getenv("VERBA_URL")

# Use the global ollama_url directly inside the function
async def invoke_llm(system_prompt, user_prompt, ollama_model):
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "model": ollama_model,
        "options": {
            "top_k": 50, 
            "top_p": 0.5, 
            "temperature": 0.7,
            "seed": 42
        },
        "stream": False
    }

    try:
        async with httpx.AsyncClient() as client:
            # Use the global ollama_url here
            response = await client.post(f"{ollama_url}/api/chat", json=payload, timeout=None)

        if response.status_code == 200:
            response_data = json.loads(response.content)
            ai_msg = response_data['message']['content']
            return {"answer": ai_msg}
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return {"error": response.text}
    except httpx.TimeoutException:
        print("Request timed out. This should not happen with unlimited timeout.")
        return {"error": "Request timed out"}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"error": str(e)}
        

def chunk_text(text, chunk_size=1000):
    """
    Splits text into semantic chunks using LangChain's RecursiveCharacterTextSplitter,
    maintaining similar output format as the original function.
    
    Args:
        text (str): The input text to be chunked
        chunk_size (int): Target size for each chunk in words (approximate)
        
    Returns:
        list: List of tuples (chunk_text, actual_chunk_size)
    """
    # Initialize the text splitter
    # Using average word length of 5 characters + 1 for space to convert words to chars
    chars_per_chunk = chunk_size * 6
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chars_per_chunk,
        chunk_overlap=50,  # Some overlap to maintain context
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    # Split the text
    raw_chunks = text_splitter.split_text(text)
    
    # Convert to required format with word counts
    chunks = []
    for chunk in raw_chunks:
        word_count = len(chunk.split())
        chunks.append((chunk, word_count))
    
    return chunks

async def summarize(thesis, topic, rubric):
    rubric_keys_string = ', '.join(rubric.keys())
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
- Significantly reduced length with no formatting.
- Maintain academic tone
- Do NOT guess. Just summarize whatever is mentioned in the dissertation chunk.
- Provide ONLY the summarized text, no filler words.
'''

        # Generate the response using the utility function
        try:
            full_text_dict = await invoke_llm(
                system_prompt=summarize_system_prompt,
                user_prompt=summarize_user_prompt,
                ollama_model='qwen2.5'
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


def get_first_n_words(text, n):
    # Split the text into words
    words = text.split()
    # Get the first 500 words
    first_n_words = words[:n]
    # Join them back into a string
    return " ".join(first_n_words)


async def extract_name(dissertation):
    
    dissertation_first_pages = get_first_n_words(dissertation, 200)

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
Name should be returned exactly as written in the text
"""
        
        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_name_system_prompt,
        user_prompt=extract_name_user_prompt,
        ollama_model = 'nemotron-mini'
    )

    name = full_text_dict["answer"]
    print("THE NAME IS IS: " + name)
    # Final response with aggregated feedback and score
    
    return name 


async def extract_topic(dissertation):
    
    dissertation_first_pages = get_first_n_words(dissertation, 150)

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
Topic should be returned exactly as written in the text
"""

        
        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_topic_system_prompt,
        user_prompt=extract_topic_user_prompt,
        ollama_model = 'nemotron-mini'
    )

    topic = full_text_dict["answer"]
    print("THE TOPIC IS: " + topic)
    # Final response with aggregated feedback and score
    
    return topic 


async def extract_degree(dissertation):
    
    dissertation_first_pages = get_first_n_words(dissertation, 200)

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

## Output Format
Degree should be returned exactly as written in the text
"""

        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_degree_system_prompt,
        user_prompt=extract_degree_user_prompt,
        ollama_model = 'nemotron-mini'
    )

    degree = full_text_dict["answer"]
    print("THE DEGREE IS: " + degree)
    
    return degree 