import os
from dotenv import load_dotenv
import aiohttp
import base64
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")
ollama_model_for_image = os.getenv("OLLAMA_MODEL_FOR_IMAGE")


async def generate_from_image(image_data: bytes, prompt: str):
    try:
        # Encode the binary image data to Base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        
        data = {
            "model": ollama_model_for_image,
            "prompt": prompt,
            "images": [encoded_image],
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{ollama_url}/api/generate", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    # print("########################################")
                    # print(result)
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Image analysis failed with status {response.status}: {error_text}")
                    return {"response": "Failed to analyze image"}
    except Exception as e:
        logger.error(f"Error in generate_from_image: {str(e)}")
        return {"response": "Failed to analyze image"}

async def analyze_image(image_data: bytes):
    image_agent_user_prompt = """
    Analyze the following image and provide a report detailing the features present. 
    Include a clear description of what is depicted in the image without any interpretation.
    Please keep the summarization below 200 words. Describe the intent of the image, not the details of what is present.
    The summarization needs to be brief and short.
    """
    return await generate_from_image(image_data, image_agent_user_prompt)
