from backend.src.utils import *
from backend.src.image_agents import *
from backend.src.agents import *
from backend.src.dissertation_types import QueryRequestThesisAndRubric, QueryRequestThesis
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn
import re
import fitz
import logging
from io import BytesIO
from docx import Document
from docx.parts.image import ImagePart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Dissertation Analysis API",
    description="API for analyzing dissertations",
    version="1.0.0"
)

ollama_model_for_analysis = os.getenv("OLLAMA_MODEL_FOR_ANALYSIS")
ollama_model_for_image = os.getenv("OLLAMA_MODEL_FOR_IMAGE")
ollama_url = os.getenv("OLLAMA_URL")

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, but you can specify a list of domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def read_root():
    return {"message": "Hello! This is the Dissertation Analysis! Dissertation Analysis app is running!"}

@app.post("/extract_text_from_file_and_analyze_images")
async def analyze_file(file: UploadFile = File(...)):
    try:
        if file.filename.endswith(".pdf"):
            return await process_pdf(file)
        elif file.filename.endswith(".docx"):
            return await process_docx(file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")
    except Exception as e:
        logger.exception("An error occurred while processing the file.")
        raise HTTPException(status_code=500, detail="Failed to process the file. Please try again.") from e


@app.post("/api/pre_analyze")
async def pre_analysis(request: QueryRequestThesis):
    print(request.thesis)
    # Process non-streaming operations first
    degree_of_student = await extract_degree_agent(request.thesis)
    name_of_author = await extract_name_agent(request.thesis)
    topic = await extract_topic_agent(request.thesis)
    summary_of_thesis = await summarize_and_analyze_agent(request.thesis, topic)

    response = {
        "degree": degree_of_student,
        "name": name_of_author,
        "topic": topic,
        "pre_analyzed_summary": summary_of_thesis
    }
    
    return response

@app.websocket("/ws/dissertation_analysis")
async def websocket_dissertation(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Receive the initial data
        data = await websocket.receive_json()
        request = QueryRequestThesisAndRubric(**data)
        degree_of_student = request.pre_analysis.degree
        name_of_author = request.pre_analysis.name
        topic = request.pre_analysis.topic
        summary_of_thesis = request.pre_analysis.pre_analyzed_summary
        # Send initial metadata
        await websocket.send_json({
            "type": "metadata",
            "data": {
                "name": name_of_author,
                "degree": degree_of_student,
                "topic": topic
            }
        })

        dissertation_system_prompt = """You are an impartial academic evaluator - an expert in analyzing the summarized dissertation provided to you. 
Your task is to assess the quality of the provided summarized dissertation in relation to specific evaluation criteria. 
You will receive both the summarized dissertation and the criteria to analyze how effectively the dissertation addresses the research topic."""

        evaluation_results = {}
        total_score = 0

        # Process each criterion
        for criterion, explanation in request.rubric.items():
            dissertation_user_prompt = f"""
# Input Materials
## Dissertation Text
{summary_of_thesis}

## Evaluation Context
- Author: {name_of_author}
- Academic Field: {degree_of_student}

## Assessment Criterion and its explanation
### {criterion}:
#### Explanation: {explanation['criteria_explanation']}

{explanation['criteria_output']}

Please make sure that you critique the work heavily, including all improvements that can be made.

DO NOT SCORE THE DISSERTATION, YOU ARE TO PROVIDE ONLY DETAILED ANALYSIS, AND NO SCORES ASSOCIATED WITH IT.
"""         
            if request.feedback:
                dissertation_user_prompt = dissertation_user_prompt + '\n' + "IMPORTANT(The following feedback was provided by an expert. Consider the feedback properly, and ensure your evaluation follows this feedback): "+ request.feedback
            # Send criterion start marker
            await websocket.send_json({
                "type": "criterion_start",
                "data": {"criterion": criterion}
            })

            # Stream the analysis
            analysis_chunks = []
            async for chunk in stream_llm(
                system_prompt=dissertation_system_prompt,
                user_prompt=dissertation_user_prompt,
                ollama_model=ollama_model_for_analysis
            ):
                analysis_chunks.append(chunk)
                await websocket.send_json({
                    "type": "analysis_chunk",
                    "data": {
                        "criterion": criterion,
                        "chunk": chunk
                    }
                })

            # Combine chunks for scoring
            analyzed_dissertation = "".join(analysis_chunks)
            
            # Get the score (non-streaming)
            graded_response = await scoring_agent(
                analyzed_dissertation, 
                criterion, 
                explanation['score_explanation'], 
                explanation['criteria_explanation'],
                request.feedback
            )

            # Extract score
            pattern = r"spanda_score\s*:\s*(?:\*{1,2}\s*)?(\d+(?:\.\d+)?)\s*(?:\*{1,2})?"
            match = re.search(pattern, graded_response, re.IGNORECASE)
            
            score = float(match.group(1)) if match else 0
            total_score += score

            # Send criterion completion
            await websocket.send_json({
                "type": "criterion_complete",
                "data": {
                    "criterion": criterion,
                    "score": score,
                    "full_analysis": analyzed_dissertation
                }
            })

            evaluation_results[criterion] = {
                "feedback": analyzed_dissertation,
                "score": score
            }
        print(evaluation_results)
        # Send final results
        await websocket.send_json({
            "type": "complete",
            "data": {
                "criteria_evaluations": evaluation_results,
                "total_score": total_score,
                "name": name_of_author,
                "degree": degree_of_student,
                "topic": topic
            }
        })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)}
        })
    finally:
        await websocket.close()


###################################################HELPER FUNCTIONS###################################################
###################################################HELPER FUNCTIONS###################################################
###################################################HELPER FUNCTIONS###################################################


async def process_pdf(pdf_file: UploadFile):
    pdf_bytes = await pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    final_text = ""

    for page_num in range(doc.page_count):
        page = doc[page_num]
        page_text = extract_and_clean_text_from_page(page)
        final_text += f"\n\n{page_text}"

        for img_index, img in enumerate(page.get_images(full=True)):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Convert image bytes to proper format and analyze
                image_analysis = await analyze_image(image_bytes)
                if isinstance(image_analysis, dict) and 'response' in image_analysis:
                    analysis_result = image_analysis['response'].strip()
                    if analysis_result:
                        final_text += f"\n\nImage {img_index + 1} Analysis: {analysis_result}"
            except Exception as e:
                logger.error(f"Failed to analyze image {img_index + 1} on page {page_num + 1}: {e}")

    logger.info(f"Preview of cleaned text and images (first 500 chars): {final_text[:500]}")
    return {"text_and_image_analysis": final_text.strip()}

async def process_docx(docx_file: UploadFile):
    docx_bytes = await docx_file.read()
    docx_stream = BytesIO(docx_bytes)
    document = Document(docx_stream)
    final_text = ""

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            cleaned_text = re.sub(r'\s+', ' ', text)
            final_text += f" {cleaned_text}"

    # Process images in DOCX
    for rel in document.part.rels.values():
        if isinstance(rel.target_part, ImagePart):
            try:
                image_bytes = rel.target_part.blob
                
                # Convert image bytes to proper format and analyze
                image_analysis = await analyze_image(image_bytes)
                if isinstance(image_analysis, dict) and 'response' in image_analysis:
                    analysis_result = image_analysis['response'].strip()
                    if analysis_result:
                        final_text += f"\n\nImage Analysis: {analysis_result}"
            except Exception as e:
                logger.error(f"Failed to analyze DOCX image: {e}")

    cleaned_text = clean_text(final_text)
    return {"text_and_image_analysis": cleaned_text.strip()}

def extract_and_clean_text_from_page(page) -> str:
    text_blocks = []
    blocks = page.get_text("blocks")
    for block in blocks:
        if isinstance(block[4], str) and block[4].strip():
            cleaned_block = ' '.join(block[4].split())
            if cleaned_block:
                text_blocks.append(cleaned_block)

    combined_text = ' '.join(text_blocks)
    cleaned_text = clean_text(combined_text)
    return cleaned_text

def clean_text(text: str) -> str:
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Chapter\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\b(?!\s*[a-zA-Z])', '', text)
    text = re.sub(r'[\r\n\t\f]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

###################################################HELPER FUNCTIONS###################################################
###################################################HELPER FUNCTIONS###################################################
###################################################HELPER FUNCTIONS###################################################


def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)

if __name__ == "__main__":
    main()