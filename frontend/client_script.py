import requests
import websockets
import asyncio
import json
# Define the file path
pdf_file_path = "/home/ctspl/Downloads/2022MT12008.pdf"
server_url = "http://localhost:8006"
# Define the rubric once
rubric = {
    "criterion1": {
        "criteria_explanation": "Thorough research relevance",
        "criteria_output": "Detailed feedback",
        "score_explanation": "Explanation of scoring based on relevance"
    },
    # Add additional criteria as needed
}
async def analyze_dissertation(pre_analysis_data, analyzed_thesis):
    async with websockets.connect(f"ws://localhost:8006/ws/dissertation_analysis") as websocket:
        # Send pre-analysis data, rubric, and analyzed_thesis
        await websocket.send(json.dumps({
            "pre_analysis": pre_analysis_data,
            "rubric": rubric,
            "feedback": "Please provide constructive feedback based on evaluation."
        }))
        # Listen for incoming messages
        while True:
            message = await websocket.recv()
            message_data = json.loads(message)
            # Handle different types of messages
            if message_data["type"] == "metadata":
                print("Dissertation Metadata:", message_data["data"])
            elif message_data["type"] == "criterion_start":
                print(f"Starting analysis for criterion: {message_data['data']['criterion']}")
            elif message_data["type"] == "analysis_chunk":
                print(f"Analysis chunk for criterion '{message_data['data']['criterion']}':", message_data["data"]["chunk"])
            elif message_data["type"] == "criterion_complete":
                print(f"Completed criterion '{message_data['data']['criterion']}' with score:", message_data["data"]["score"])
            elif message_data["type"] == "complete":
                print("Final Results:", message_data["data"])
                break
            elif message_data["type"] == "error":
                print("Error:", message_data["data"]["message"])
                break
def extract_text_and_images(pdf_file_path):
    # Step 1: Extract text and images
    with open(pdf_file_path, 'rb') as pdf_file:
        response = requests.post(
            f"{server_url}/extract_text_from_pdf_and_analyze_images",
            files={"pdf_file": pdf_file}
        )
    if response.status_code == 200:
        print("Text and image analysis extracted successfully.")
        return response.json()
    else:
        print("Failed to extract text and images:", response.text)
        return None
def pre_analyze_text(extracted_data):
    # Step 2: Pre-analyze extracted text
    thesis_text = extracted_data.get("text_and_image_analysis", "")
    request_data = {
        "thesis": thesis_text,
        "rubric": rubric
    }
    response = requests.post(f"{server_url}/api/pre_analyze", json=request_data)
    if response.status_code == 200:
        print("Pre-analysis completed successfully.")
        return response.json(), thesis_text
    else:
        print("Failed to pre-analyze text:", response.text)
        return None, None
# Main function to coordinate the steps
async def main():
    extracted_data = extract_text_and_images(pdf_file_path)
    if extracted_data:
        pre_analysis_data, analyzed_thesis = pre_analyze_text(extracted_data)
        if pre_analysis_data:
            await analyze_dissertation(pre_analysis_data, analyzed_thesis)
# Run the main function
asyncio.run(main())










