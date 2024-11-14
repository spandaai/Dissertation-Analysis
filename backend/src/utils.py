import json
import httpx
import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import AsyncGenerator, List
from typing import AsyncGenerator, Optional
from enum import Enum

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")
vllm_url = os.getenv("VLLM_URL")


class ModelType(Enum):
    ANALYSIS = "ANALYSIS"
    EXTRACTION = "EXTRACTION"
    SUMMARY = "SUMMARY"
    IMAGE = "IMAGE"
    SCORING = "SCORING"

class EnvConfig:
    def __init__(self):
        # VLLM Configuration
        self.vllm_url = os.getenv("VLLM_URL")
        self.vllm_models = {
            ModelType.ANALYSIS: os.getenv("VLLM_MODEL_FOR_ANALYSIS"),
            ModelType.EXTRACTION: os.getenv("VLLM_MODEL_FOR_EXTRACTION"),
            ModelType.SUMMARY: os.getenv("VLLM_MODEL_FOR_SUMMARY"),
            ModelType.IMAGE: os.getenv("VLLM_MODEL_FOR_IMAGE"),
            ModelType.SCORING: os.getenv("VLLM_MODEL_FOR_SCORING"),
        }
        
        # Ollama Configuration
        self.ollama_url = os.getenv("OLLAMA_URL")
        self.ollama_models = {
            ModelType.ANALYSIS: os.getenv("OLLAMA_MODEL_FOR_ANALYSIS"),
            ModelType.EXTRACTION: os.getenv("OLLAMA_MODEL_FOR_EXTRACTION"),
            ModelType.SUMMARY: os.getenv("OLLAMA_MODEL_FOR_SUMMARY"),
            ModelType.IMAGE: os.getenv("OLLAMA_MODEL_FOR_IMAGE"),
            ModelType.SCORING: os.getenv("OLLAMA_MODEL_FOR_SCORING"),

        }
    
    def is_vllm_available(self, model_type: ModelType) -> bool:
        """Check if VLLM is configured and available for specific model type"""
        return bool(self.vllm_url and self.vllm_models.get(model_type))
    
    def is_ollama_available(self, model_type: ModelType) -> bool:
        """Check if Ollama is configured and available for specific model type"""
        return bool(self.ollama_url and self.ollama_models.get(model_type))
    
    def get_model_and_url(self, model_type: ModelType) -> tuple[Optional[str], Optional[str]]:
        """Get the appropriate model and URL based on availability"""
        # First try VLLM
        if self.is_vllm_available(model_type):
            return self.vllm_models[model_type], self.vllm_url
        # Then try Ollama
        elif self.is_ollama_available(model_type):
            return self.ollama_models[model_type], self.ollama_url
        return None, None

async def invoke_llm(
    system_prompt: str,
    user_prompt: str,
    model_type: ModelType,
    config: Optional[EnvConfig] = None
) -> dict:
    """
    Unified interface for invoking LLM models. Automatically chooses between VLLM and Ollama
    based on availability, with priority given to VLLM.
    """
    if config is None:
        config = EnvConfig()
    
    model, url = config.get_model_and_url(model_type)
    
    if not model or not url:
        return {"error": f"No LLM service available for model type {model_type.value}"}
    
    if config.is_vllm_available(model_type) and url == config.vllm_url:
        return await invoke_llm_vllm(system_prompt, user_prompt, model)
    else:
        return await invoke_llm_ollama(system_prompt, user_prompt, model)

async def stream_llm(
    system_prompt: str,
    user_prompt: str,
    model_type: ModelType,
    config: Optional[EnvConfig] = None
) -> AsyncGenerator[str, None]:
    """
    Unified interface for streaming LLM responses. Automatically chooses between VLLM and Ollama
    based on availability, with priority given to VLLM.
    """
    if config is None:
        config = EnvConfig()
    
    model, url = config.get_model_and_url(model_type)
    
    if not model or not url:
        yield f"Error: No LLM service available for model type {model_type.value}"
        return
    
    if config.is_vllm_available(model_type) and url == config.vllm_url:
        async for chunk in stream_llm_vllm(system_prompt, user_prompt, model):
            yield chunk
    else:
        async for chunk in stream_llm_ollama(system_prompt, user_prompt, model):
            yield chunk

            
##############################################################################################################################
##############################################################################################################################
################################################VLLM GENERATION FUNCTIONS START###############################################
##############################################################################################################################


async def stream_llm_vllm(system_prompt: str, user_prompt: str, ollama_model: str) -> AsyncGenerator[str, None]:
    """Stream responses from the LLM for the dissertation analysis."""
    
    # Define the payload for the request
    payload = {
        "model": ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": True
    }

    async with httpx.AsyncClient() as client:
        # Send the POST request to the Ollama API
        async with client.stream('POST', vllm_url, json=payload, timeout=None) as response:
            # Check for a successful response
            if response.status_code == 200:
                async for line in response.aiter_lines():
                    if line:
                        # Remove the "data:" prefix if present
                        raw_line = line.lstrip("data: ").strip()
                        
                        # Check for the 'DONE' signal to complete the stream
                        if raw_line == "[DONE]":
                            break  # Exit when the streaming completes
                        
                        try:
                            # Parse the cleaned-up line as JSON
                            data = json.loads(raw_line)
                            
                            # Extract and yield the content from 'choices' in the response
                            content = data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            if content:
                                yield content  # Yield the content chunk
                        except json.JSONDecodeError:
                            continue  # Ignore invalid JSON lines
            else:
                print(f"Request failed with status code {response.status_code}")


async def invoke_llm_vllm(system_prompt: str, user_prompt: str, ollama_model: str) -> dict:
    """Invoke the LLM and return the final non-streaming response."""
    prompt = f"""
    {system_prompt}
    {user_prompt}
    """
    
    # Define the payload for the request
    payload = {
        "model": ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False  # Set stream to False for non-streaming
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Send the POST request to the Ollama API
            response = await client.post(vllm_url, json=payload, timeout=None)
            
            # Check for a successful response
            if response.status_code == 200:
                response_data = json.loads(response.content)
                ai_msg = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return {"answer": ai_msg}  # Return the final answer
            else:
                # Handle unsuccessful responses
                print(f"Error: {response.status_code} - {response.text}")
                return {"error": response.text}
    
    except httpx.TimeoutException:
        print("Request timed out.")
        return {"error": "Request timed out"}
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"error": str(e)}
    

##############################################################################################################################
##############################################################################################################################
################################################VLLM GENERATION FUNCTIONS STOP################################################
##############################################################################################################################



##############################################################################################################################
##############################################################################################################################
################################################OLLAMA GENERATION FUNCTIONS START#############################################
##############################################################################################################################

# Use the global ollama_url directly inside the function
async def invoke_llm_ollama(system_prompt, user_prompt, ollama_model):
    prompt = f"""
{system_prompt}

{user_prompt}
"""
    payload = {
        # "messages": [
        #     {"role": "system", "content": system_prompt},
        #     {"role": "user", "content": user_prompt}
        # ],
        "prompt": prompt,
        "model": ollama_model,
        "options": {
            "top_k": 1, 
            "top_p": 0, 
            "temperature": 0,
            "seed": 100
        },
        "stream": False
    }

    try:
        async with httpx.AsyncClient() as client:
            # Use the global ollama_url here
            response = await client.post(f"{ollama_url}/api/generate", json=payload, timeout=None)
            response_data = json.loads(response.content)

        if response.status_code == 200:
            ai_msg = response_data['response']
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



async def stream_llm_ollama(system_prompt: str, user_prompt: str, ollama_model: str) -> AsyncGenerator[str, None]:
    """Stream responses from the LLM"""
    prompt = f"""
    {system_prompt}
    {user_prompt}
    """
    payload = {
        "prompt": prompt,
        "model": ollama_model,
        "options": {
            "top_k": 1,
            "top_p": 0,
            "temperature": 0,
            "seed": 100
        },
        "stream": True
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream('POST', f"{ollama_url}/api/generate", json=payload, timeout=None) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            yield data['response']
                    except json.JSONDecodeError:
                        continue


##############################################################################################################################
##############################################################################################################################
################################################OLLAMA GENERATION FUNCTIONS STOP##############################################
##############################################################################################################################



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
        chunk_overlap=0,  # Some overlap to maintain context
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

def get_first_n_words(text, n):
    # Split the text into words
    words = text.split()
    # Get the first 500 words
    first_n_words = words[:n]
    # Join them back into a string
    return " ".join(first_n_words)


