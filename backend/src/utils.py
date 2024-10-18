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
        
