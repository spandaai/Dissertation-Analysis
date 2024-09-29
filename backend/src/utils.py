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

# Define the OllamaLLM class with flexibility to input system and user prompts
class OllamaLLM(LLM):
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt  # Set system prompt during initialization

    async def _invoke_llm(self, user_prompt: str) -> str:
        # Use the global ollama_url and the system prompt from initialization
        return await invoke_llm(self.system_prompt, user_prompt)

    def _call(self, prompt: str, stop: Optional[list[str]] = None) -> str:
        # Call the asynchronous invoke_llm in a synchronous manner
        response = asyncio.run(self._invoke_llm(prompt))
        return response["answer"]

    @property
    def _llm_type(self) -> str:
        return "ollama_llm"

# Use the global ollama_url directly inside the function
async def invoke_llm(system_prompt, user_prompt):
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
            print("RESPONSE DATA:")
            print(response_data)
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
        

async def call_spanda_retrieve(payload):
    url = f"{verba_url}/api/query"

    request_data = payload

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(url, json=request_data)

        # Check if the response was successful
        if response.status_code == 200:
            is_response_relevant = response.json()
            return is_response_relevant
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        

async def response_relevance_filter_for_chatbot(query: str, response: str) -> str:
    evaluate_system_prompt = """You are given a query and a response. Determine if the response is relevant, irrelevant, or highly irrelevant to the query. Only respond with "Relevant", "Irrelevant", or "Highly Irrelevant"."""

    evaluate_user_prompt = f"""
        Query: {query}

        Content: {response}
    """
    
    # Call the spanda_generate endpoint with unpacked generation_payload
    is_response_relevant_dict = await call_spanda_generate(
        system_prompt=evaluate_system_prompt,
        user_prompt=evaluate_user_prompt,
        user_input=query,
        context=" "
    )
    is_response_relevant = is_response_relevant_dict["answer"]
    print("RESPONSE FROM BACKEND: ")
    print(is_response_relevant)
    if is_response_relevant.lower() == 'highly irrelevant':
        return "Given that the answer that I am able to retrieve with the information I have seems to be highly irrelevant to the query, I abstain from providing a response. I am sorry for not being helpful." # Returns an empty coroutine
    elif is_response_relevant.lower() == 'irrelevant':
        return "The answer I am able to retrieve with the information I have seems to be irrelevant to the query. Nevertheless, I will provide you with the response in the hope that it will be valuable. Apologies in advance if it turns out to be of no value: " + response
    return response


async def context_relevance_filter(query: str, context: str) -> str:
    evaluate_system_prompt = (
        """You are an AI responsible for assessing whether the provided content is relevant to a specific query. Carefully analyze the content and determine if it directly addresses or provides pertinent information related to the query. Only respond with "YES" if the content is relevant, or "NO" if it is not. Do not provide any explanations, scores, or additional text—just a single word: "YES" or "NO"."""
    )
    evaluate_user_prompt = (
        f"""
        Content: {context}

        Query: {query}

        You are an AI responsible for assessing whether the provided content is relevant to a specific query. Carefully analyze the content and determine if it directly addresses or provides pertinent information related to the query. Only respond with "YES" if the content is relevant, or "NO" if it is not. Do not provide any explanations, scores, or additional text—just a single word: "YES" or "NO".
        """
    )

    is_context_relevant_dict = await call_spanda_generate(
        system_prompt=evaluate_system_prompt,
        user_prompt=evaluate_user_prompt,
        user_input=query,
        context=context
    )
    is_context_relevant = is_context_relevant_dict["answer"]
    # print("Is this context relevant? ")
    print("Is this context relevant? " + is_context_relevant)
    if is_context_relevant.lower() == 'no':
        return " "  # Returns an empty coroutine
    return context



# async def main():
#     # Sample query and response to test the function
#     query = "What is the capital of France?"
#     response_content = "The capital of France is Paris."

#     # Call the response relevance filter
#     result = await response_relevance_filter_for_chatbot(query, response_content)

#     # Print the result
#     print("Final Response:", result)

# # Run the main function in an asyncio event loop
# if __name__ == "__main__":
#     asyncio.run(main())