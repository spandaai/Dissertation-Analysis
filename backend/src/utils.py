import asyncio
import httpx

async def call_spanda_generate(system_prompt: str, user_prompt: str, user_input: str, context: str):
    url = "http://localhost:8000/api/spandagenerate"
    request_data = {
        "user_input": user_input,
        "context": context,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt
    }

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(url, json=request_data)

        # Check if the response was successful
        if response.status_code == 200:
            is_response_relevant = response.json()
            return is_response_relevant
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        

async def call_spanda_retrieve(payload):
    url = "http://localhost:8000/api/query"

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