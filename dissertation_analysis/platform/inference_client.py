import json
import os
import httpx
from typing import AsyncGenerator, List, Dict, Any
import aiohttp
import base64
import logging
from dotenv import load_dotenv
from dissertation_analysis.common.configs import CancellationToken

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

vllm_url_for_image = os.getenv("VLLM_URL_FOR_IMAGE")
vllm_model_for_image = os.getenv("VLLM_MODEL_FOR_IMAGE")

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")
ollama_model_for_image = os.getenv("OLLAMA_MODEL_FOR_IMAGE")

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")
vllm_url = os.getenv("VLLM_URL_FOR_ANALYSIS")

        
##############################################################################################################################
##############################################################################################################################
###############################################VLLM GENERATION FUNCTIONS START################################################
##############################################################################################################################

async def invoke_llm_vllm(
    system_prompt: str, 
    user_prompt: str, 
    ollama_model: str,
    vllm_url: str,
    temperature: float = 0.0, 
    top_p: float = 0.1,
    top_k: int = 1,   
    seed: int = 42
) -> dict:
    """Invoke the LLM with specified sampling parameters and return the final non-streaming response."""
    
    # Create the full prompt
    prompt = f"""
    {system_prompt}
    {user_prompt}
    """
    
    # Define the payload for the request with sampling parameters
    payload = {
        "model": ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "seed": seed,
        "stream": False  # Set stream to False for non-streaming
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Use the provided VLLM URL
            response = await client.post(vllm_url, json=payload, timeout=None)
            
            if response.status_code == 200:
                response_data = json.loads(response.content)
                ai_msg = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return {"answer": ai_msg}
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return {"error": response.text}
    
    except httpx.TimeoutException:
        print("Request timed out.")
        return {"error": "Request timed out"}
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"error": str(e)}
    

async def stream_llm_vllm(
    system_prompt: str, 
    user_prompt: str, 
    ollama_model: str,
    vllm_url: str,
    cancellation_token: CancellationToken,
    temperature: float = 0.0,
    top_p: float = 0.1,
    top_k: int = 1,   
    seed: int = 42
) -> AsyncGenerator[str, None]:
    """Stream responses from the LLM with cancellation support"""
    
    payload = {
        "model": ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "seed": seed,
        "stream": True
    }

    async with httpx.AsyncClient() as client:
        try:
            async with client.stream('POST', vllm_url, json=payload, timeout=None) as response:
                if response.status_code == 200:
                    async for line in response.aiter_lines():
                        if cancellation_token.is_cancelled:
                            # Close the connection explicitly
                            await response.aclose()
                            break
                            
                        if line:
                            raw_line = line.lstrip("data: ").strip()
                            
                            if raw_line == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(raw_line)
                                content = data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                else:
                    print(f"Request failed with status code {response.status_code}")
        except Exception as e:
            print(f"Error during streaming: {str(e)}")
            raise

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
            "seed": 100,
            "num_ctx": 4096
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


async def stream_llm_ollama(
    system_prompt: str, 
    user_prompt: str, 
    ollama_model: str,
    cancellation_token: CancellationToken
) -> AsyncGenerator[str, None]:
    """Stream responses from Ollama with cancellation support"""
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
            "seed": 100,
            "num_ctx": 4096
        },
        "stream": True
    }
    
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream('POST', f"{ollama_url}/api/generate", json=payload, timeout=None) as response:
                async for line in response.aiter_lines():
                    if cancellation_token.is_cancelled:
                        # Close the connection explicitly
                        await response.aclose()
                        break
                        
                    if line:
                        try:
                            data = json.loads(line)
                            if 'response' in data:
                                yield data['response']
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error during streaming: {str(e)}")
            raise



##############################################################################################################################
##############################################################################################################################
################################################OLLAMA GENERATION FUNCTIONS STOP##############################################
##############################################################################################################################



async def generate_from_image_ollama(image_data: bytes, prompt: str):
    try:
        # Encode the binary image data to Base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        
        data = {
            "model": ollama_model_for_image,
            "prompt": prompt,
            "images": [encoded_image],
            "options": {
                "top_k": 1, 
                "top_p": 0, 
                "temperature": 0,
                "seed": 100
            },
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{ollama_url}/api/generate", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print("########################################")
                    print(result)
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Image analysis failed with status {response.status}: {error_text}")
                    return {"response": "Failed to analyze image"}
    except Exception as e:
        logger.error(f"Error in generate_from_image: {str(e)}")
        return {"response": "Failed to analyze image"}



async def generate_from_image(
    image_data: bytes,
    prompt: str,
    model: str = vllm_model_for_image,
    base_url: str = vllm_url_for_image
) -> Dict[str, Any]:
    """
    Generate response from image using custom API format
    
    Args:
        image_data: Image bytes
        prompt: The prompt text
        model: Model identifier
        base_url: API base URL
    
    Returns:
        Dict containing the response
    """
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]

    try:
        response = await send_multimodal_chat_message(
            messages=messages,
            image_bytes=image_data,
            model=model,
            base_url=base_url
        )
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in generate_from_image: {str(e)}")
        return {"response": "Failed to analyze image"}


async def send_multimodal_chat_message(
    messages: List[Dict[str, Any]],
    image_bytes: bytes = None,
    model: str = "Qwen/Qwen2-VL-2B-Instruct-AWQ",
    base_url: str = "http://localhost:8002/v1/chat/completions"
) -> str:
    """
    Send a multi-modal chat message with optional image bytes to the API endpoint.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        image_bytes: Optional image data as bytes
        model: The model identifier to use
        base_url: Base URL of the API server
    
    Returns:
        The response text from the model
    """
    endpoint = f"{base_url}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if image_bytes:
        try:
            base64_image = await encode_bytes_to_base64(image_bytes)
            for msg in reversed(messages):
                if msg["role"] == "user":
                    msg["content"].append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    )
                    break
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "top_p": 0.1,
        "top_k": 1,
        "seed": 42,
        "stream": False
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed with status {response.status}: {error_text}")
                    raise aiohttp.ClientError(f"API request failed: {error_text}")
                    
    except Exception as e:
        logger.error(f"Error making API request: {str(e)}")
        raise


###############################################################################################################################################################
###############################################################################################################################################################
#########################################VLLM IMAGE AGENT###############################################################################################
###############################################################################################################################################################

async def analyze_image_vllm(
    image_data: bytes,
    model: str = vllm_model_for_image,
    base_url: str = vllm_url_for_image
) -> Dict[str, Any]:
    """
    Analyze image using predefined prompt
    
    Args:
        image_data: Image bytes
        model: Model identifier
        base_url: API base URL
    
    Returns:
        Dict containing the analysis response
    """

    image_agent_user_prompt = """
    Analyze the following image and provide a report detailing the features present. 
    Include a clear description of what is depicted in the image without any interpretation.
    Please keep the summarization below 200 words. Describe the intent of the image, not the details of what is present.
    The summarization needs to be brief and short.
    """
    
    return await generate_from_image(
        image_data=image_data,
        prompt=image_agent_user_prompt,
        model=model,
        base_url=base_url
    )

###############################################################################################################################################################
#########################################OLLAMA IMAGE AGENT####################################################################################################
###############################################################################################################################################################
###############################################################################################################################################################


async def analyze_image_ollama(image_data: bytes):
    image_agent_user_prompt = """
    Analyze the following image and provide a report detailing the features present. 
    Include a clear description of what is depicted in the image without any interpretation.
    Please keep the summarization below 200 words. Describe the intent of the image, not the details of what is present.
    The summarization needs to be brief and short.
    """
    return await generate_from_image_ollama(image_data, image_agent_user_prompt)

async def encode_bytes_to_base64(image_bytes: bytes) -> str:
    """
    Encode image bytes to base64 string.
    
    Args:
        image_bytes: Image data as bytes
    
    Returns:
        Base64 encoded string of the image
    """
    try:
        return base64.b64encode(image_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image: {str(e)}")
        raise