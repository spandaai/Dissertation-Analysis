from dotenv import load_dotenv
from enum import Enum
import httpx
import json
from langchain_core.language_models.llms import LLM
import os
from pydantic import BaseModel, Field
from typing import AsyncGenerator, Optional


# Load environment variables from .env file
load_dotenv()

# Access the environment variables
# ollama_url = os.getenv("OLLAMA_URL")
# vllm_url = os.getenv("VLLM_URL_FOR_ANALYSIS")


class CancellationToken:
    def __init__(self):
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

class ModelType(Enum):
    ANALYSIS = "ANALYSIS"
    EXTRACTION = "EXTRACTION"
    SUMMARY = "SUMMARY"
    IMAGE = "IMAGE"
    SCORING = "SCORING"

class UrlType(Enum):
    ANALYSIS = "ANALYSIS"
    EXTRACTION = "EXTRACTION"
    SUMMARY = "SUMMARY"
    IMAGE = "IMAGE"
    SCORING = "SCORING"

class EnvConfig:
    def __init__(self):
        # VLLM Configuration
        self.vllm_url = os.getenv("VLLM_MODEL_FOR_ANALYSIS")
        self.vllm_models = {
            ModelType.ANALYSIS: os.getenv("VLLM_MODEL_FOR_ANALYSIS"),
            ModelType.EXTRACTION: os.getenv("VLLM_MODEL_FOR_EXTRACTION"),
            ModelType.SUMMARY: os.getenv("VLLM_MODEL_FOR_SUMMARY"),
            ModelType.IMAGE: os.getenv("VLLM_MODEL_FOR_IMAGE"),
            ModelType.SCORING: os.getenv("VLLM_MODEL_FOR_SCORING"),
        }
        self.vllm_urls = {
            UrlType.ANALYSIS: os.getenv("VLLM_URL_FOR_ANALYSIS"),
            UrlType.EXTRACTION: os.getenv("VLLM_URL_FOR_EXTRACTION"),
            UrlType.SUMMARY: os.getenv("VLLM_URL_FOR_SUMMARY"),
            UrlType.IMAGE: os.getenv("VLLM_URL_FOR_IMAGE"),
            UrlType.SCORING: os.getenv("VLLM_URL_FOR_SCORING"),
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
        url_type = UrlType[model_type.value]  # Convert ModelType to corresponding UrlType
        return bool(self.vllm_urls.get(url_type) and self.vllm_models.get(model_type))
    
    def is_ollama_available(self, model_type: ModelType) -> bool:
        """Check if Ollama is configured and available for specific model type"""
        return bool(self.ollama_url and self.ollama_models.get(model_type))
    
    def get_model_and_url(self, model_type: ModelType) -> tuple[Optional[str], Optional[str]]:
        """Get the appropriate model and URL based on availability"""
        # First try VLLM
        if self.is_vllm_available(model_type):
            url_type = UrlType[model_type.value]  # Convert ModelType to corresponding UrlType
            return self.vllm_models[model_type], self.vllm_urls[url_type]
        # Then try Ollama
        elif self.is_ollama_available(model_type):
            return self.ollama_models[model_type], self.ollama_url
        return None, None


class SpandaLLM(LLM, BaseModel):
    model_type: ModelType = Field(..., description="Model type for the LLM")
    system_prompt: str = Field(..., description="System prompt for the LLM")
    config: Optional[EnvConfig] = None
    model: str | None = None
    url: str | None = None

    def __init__(self, model_type: ModelType, system_prompt: str, config: Optional[EnvConfig] = None):
        super().__init__(model_type=model_type, system_prompt=system_prompt, config=config)
        # self.model_type = model_type
        # self.system_prompt = system_prompt
        self.config = config if config else EnvConfig()
        self.model, self.url = self.config.get_model_and_url(model_type)
        if not self.model or not self.url:
            raise ValueError(f"No LLM service available for model type {model_type.value}")
    
    def _llm_type(self) -> str:
        return f"""model_type: {self.model_type}
        model: {self.model}
        url: {self.url}
        system_prompt: {self.system_prompt}"""

    async def _acall(self, prompt: str, **kwargs) -> str:
        """Asynchronous call to the LLM"""
        if self.config.is_vllm_available(self.model_type):
            return await self.invoke_llm_vllm(prompt)
        else:
            return await self.invoke_llm_ollama(prompt)
        
    def _call(self, prompt: str, **kwargs) -> str:
        """Synchronous call to the LLM"""
        # This method is not implemented for simplicity
        raise NotImplementedError("Synchronous call is not implemented. Use _acall instead.")
    
    async def _astream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Asynchronous streaming call to the LLM"""
        cancellation_token = kwargs.get("cancellation_token", CancellationToken())
        if self.config.is_vllm_available(self.model_type):
            async for chunk in self.stream_llm_vllm(prompt, cancellation_token):
                yield chunk
        else:
            async for chunk in self.stream_llm_ollama(prompt, cancellation_token):
                yield chunk
    
    async def invoke_llm_vllm(
        self,
        user_prompt: str,
        temperature: float = 0.0, 
        top_p: float = 0.1,
        top_k: int = 1,   
        seed: int = 42
    ) -> str:
        """Invoke the LLM with specified sampling parameters and return the final non-streaming response."""
        system_prompt = self.system_prompt
        vllm_model = self.model
        vllm_url = self.url
        
        # Define the payload for the request with sampling parameters
        payload = {
            "model": vllm_model,
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
                    return ai_msg
                else:
                    print(f"Error: {response.status_code} - {response.text}")
                    return response.text
        
        except httpx.TimeoutException:
            print("Request timed out.")
            return "Request timed out"
        
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return str(e)

    async def stream_llm_vllm(
        self,
        user_prompt: str,
        cancellation_token: CancellationToken,
        temperature: float = 0.0,
        top_p: float = 0.1,
        top_k: int = 1,   
        seed: int = 42
    ) -> AsyncGenerator[str, None]:
        """Stream responses from the LLM with cancellation support"""
        system_prompt = self.system_prompt
        vllm_model = self.model
        vllm_url = self.url
        
        payload = {
            "model": vllm_model,
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

    async def invoke_llm_ollama(self, user_prompt):
        system_prompt = self.system_prompt
        ollama_model = self.model
        ollama_url = self.url

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
                return ai_msg
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return response.text
        except httpx.TimeoutException:
            print("Request timed out. This should not happen with unlimited timeout.")
            return "Request timed out"
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return str(e)

    async def stream_llm_ollama(
        self, 
        user_prompt: str,
        cancellation_token: CancellationToken
    ) -> AsyncGenerator[str, None]:
        """Stream responses from Ollama with cancellation support"""
        system_prompt = self.system_prompt
        ollama_model = self.model
        ollama_url = self.url
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
    
    if config.is_vllm_available(model_type):
        return await invoke_llm_vllm(system_prompt, user_prompt, model, url)
    else:
        return await invoke_llm_ollama(system_prompt, user_prompt, model)
    
    
async def stream_llm(
    system_prompt: str,
    user_prompt: str,
    model_type: ModelType,
    cancellation_token: CancellationToken,
    config: Optional[EnvConfig] = None
) -> AsyncGenerator[str, None]:
    """Unified streaming interface with cancellation support"""
    if config is None:
        config = EnvConfig()
    
    model, url = config.get_model_and_url(model_type)
    
    if not model or not url:
        yield f"Error: No LLM service available for model type {model_type.value}"
        return
    
    if config.is_vllm_available(model_type):
        async for chunk in stream_llm_vllm(system_prompt, user_prompt, model, url, cancellation_token):
            yield chunk
    else:
        async for chunk in stream_llm_ollama(system_prompt, user_prompt, model, cancellation_token):
            yield chunk

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