import logging
import os
from dotenv import load_dotenv
from typing import AsyncGenerator, Optional, Dict, Any

from dissertation_analysis.platform.inference_client import invoke_llm_ollama, invoke_llm_vllm, stream_llm_ollama, stream_llm_vllm, analyze_image_ollama, analyze_image_vllm
from dissertation_analysis.common.configs import ModelType, EnvConfig, CancellationToken

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

vllm_url_for_image = os.getenv("VLLM_URL_FOR_IMAGE")
vllm_model_for_image = os.getenv("VLLM_MODEL_FOR_IMAGE")

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")
ollama_model_for_image = os.getenv("OLLAMA_MODEL_FOR_IMAGE")

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

# choose agent
async def analyze_image(image_data: bytes) -> Dict[str, Any]:
    """
    Unified method to analyze images using either VLLM or Ollama based on available environment variables.
    VLLM takes precedence if both are configured.
    
    Args:
        image_data: Image bytes to analyze
        
    Returns:
        Dict containing the analysis response
    
    Raises:
        ValueError: If neither VLLM nor Ollama environment variables are configured
    """
    # Check VLLM configuration
    has_vllm = all([
        vllm_url_for_image,
        vllm_model_for_image
    ])
    
    # Check Ollama configuration
    has_ollama = all([
        ollama_url,
        ollama_model_for_image
    ])
    
    # If neither service is configured, raise error
    if not (has_vllm or has_ollama):
        raise ValueError(
            "No image analysis service configured. Please set either VLLM "
            "(VLLM_URL_FOR_IMAGE, VLLM_MODEL_FOR_IMAGE) or Ollama "
            "(OLLAMA_URL, OLLAMA_MODEL_FOR_IMAGE) environment variables."
        )
    
    try:
        # Prefer VLLM if available
        if has_vllm:
            logger.info("Using VLLM for image analysis")
            return await analyze_image_vllm(image_data)
        else:
            logger.info("Using Ollama for image analysis")
            return await analyze_image_ollama(image_data)
            
    except Exception as e:
        logger.error(f"Error in analyze_image: {str(e)}")
        return {"response": f"Failed to analyze image: {str(e)}"}