"""
This module provides unified interfaces for invoking and streaming interactions with 
Large Language Models (LLMs) such as VLLM and Ollama. It abstracts the logic for selecting 
the appropriate model based on availability and configuration, ensuring seamless integration 
with different backends.

Main Functions:
---------------
1. invoke_llm(system_prompt: str, user_prompt: str, model_type: ModelType, config: Optional[EnvConfig])
   - Invokes the appropriate LLM (VLLM or Ollama) for a given system prompt and user input.
   - Returns the generated response as a dictionary.

2. stream_llm(system_prompt: str, user_prompt: str, model_type: ModelType, cancellation_token: CancellationToken, config: Optional[EnvConfig])
   - Streams the LLM output in chunks for real-time interaction.
   - Supports cancellation through the provided CancellationToken.
"""


import logging
from dotenv import load_dotenv
from typing import AsyncGenerator, Optional

from dissertation_analysis.domain.inference_client import invoke_llm_ollama, invoke_llm_vllm, stream_llm_ollama, stream_llm_vllm

from dissertation_analysis.common.configs import ModelType, EnvConfig
from dissertation_analysis.common.types import CancellationToken

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

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
