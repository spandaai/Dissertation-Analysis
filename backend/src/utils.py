import json
import httpx
from langchain.llms.base import LLM
from typing import Optional
import asyncio
import os
from dotenv import load_dotenv

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
            "top_k": 1, 
            "top_p": 1, 
            "temperature": 0, 
            "seed": 100,
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
            print(ai_msg)
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
        


async def summarize(thesis):
    summarize_system_prompt = (
    """
You are an expert summarizer specializing in academic dissertations. Your goal is to produce a clear, concise summary that captures the most important details, names, dates, key points, and arguments from the dissertation. 
While focusing on brevity and clarity, ensure that each relevant section and its significance is maintained, and critical nuances are preserved. Avoid unnecessary details and redundant phrases, while keeping the essential structure and flow of the original content.
Do not use introductory language like 'this is a summary' or 'here is my'—focus directly on the content.
    """
    )

    topic = extract_topic(thesis)

    def chunk_text(text, chunk_size=1000):
        # Split the text into words
        words = text.split()
        # Generate chunks of the specified size
        for i in range(0, len(words), chunk_size):
            yield " ".join(words[i:i + chunk_size])

    # Chunk the input text
    chunks = list(chunk_text(thesis, chunk_size=1000))

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
The topic of the dissertation is {topic}. Clearly mention the topic. Note that this is just one section, and more chunks will be provided. Do not treat this as the complete dissertation.
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
    response = final_summary

    return response

def get_first_500_words(text):
    # Split the text into words
    words = text.split()
    # Get the first 500 words
    first_500_words = words[:500]
    # Join them back into a string
    return " ".join(first_500_words)

async def extract_topic(dissertation):
    
    dissertation_first_pages = get_first_500_words(dissertation)

    extract_topic_system_prompt = """
You are an expert in analyzing academic dissertations and extracting their main topics. Your task is to read the first few pages of a dissertation and identify the primary topic being discussed. Focus on understanding the main subject, research area, and key terms that best describe the topic.

Respond only with the extracted topic in a concise and clear manner, without any additional explanation or comments.
"""

    extract_topic_user_prompt = f"""
Please extract the main topic from the following text. The text contains the first few pages of a dissertation:

{dissertation_first_pages}

Respond ONLY with the extracted topic in a concise and clear manner, without any additional explanation or comments. The response must have ONLY the topic.
"""
        
        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_topic_system_prompt,
        user_prompt=extract_topic_user_prompt,
        ollama_model = 'nemotron-mini'
    )

    topic = full_text_dict["answer"]

    # Final response with aggregated feedback and score
    response = {
        "topic": topic,
    }
    
    return response   

