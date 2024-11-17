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
import io
import PyPDF2
from pdf2image import convert_from_bytes
from PIL import Image
from typing import Dict, Tuple
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Dissertation Analysis API",
    description="API for analyzing dissertations",
    version="1.0.0"
)

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
    try:
        # Process initial agents in batch
        initial_results = await process_initial_agents(request.thesis)
        
        # Use the topic from batch results for summary
        summary_of_thesis = await summarize_and_analyze_agent(
            request.thesis, 
            initial_results["topic"]
        )
        
        response = {
            "degree": initial_results["degree"],
            "name": initial_results["name"],
            "topic": initial_results["topic"],
            "pre_analyzed_summary": summary_of_thesis
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to pre-analyze thesis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to pre-analyze thesis"
        )


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
                model_type=ModelType.ANALYSIS
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


async def process_images_in_batch(images_data: List[Tuple[int, bytes]], batch_size: int = 10) -> List[Tuple[int, str]]:
    """
    Process multiple images in batches asynchronously.
    
    Args:
        images_data: List of tuples containing (page_number, image_bytes)
        batch_size: Number of images to process in each batch
        
    Returns:
        List of tuples containing (page_number, analysis_result)
    """
    results = []
    
    for i in range(0, len(images_data), batch_size):
        batch = images_data[i:i + batch_size]
        batch_tasks = [analyze_image(img_bytes) for _, img_bytes in batch]
        
        # Process batch concurrently
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Pair results with their page numbers
        for (page_num, _), result in zip(batch, batch_results):
            if isinstance(result, Exception):
                logger.error(f"Failed to analyze image on page {page_num}: {result}")
                continue
                
            if isinstance(result, dict) and 'response' in result:
                analysis_result = result['response'].strip()
                if analysis_result:
                    results.append((page_num, analysis_result))
    
    return results

async def process_pdf(pdf_file: UploadFile) -> Dict[str, str]:
    """
    Process a PDF file to extract text and analyze images after page 6.
    """
    pdf_bytes = await pdf_file.read()
    final_text = ""
    
    # Process text using PyPDF2
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    
    # Extract text from all pages
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        if text:
            final_text += f"\n\n{clean_text(text)}"
    
    # Process images only after page 6
    if len(pdf_reader.pages) > 6:
        try:
            # Convert PDF pages to images
            images = convert_from_bytes(
                pdf_bytes,
                first_page=7,
                last_page=len(pdf_reader.pages)
            )
            
            # Prepare batch data
            images_data = []
            for i, image in enumerate(images, start=7):
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                images_data.append((i, img_byte_arr.getvalue()))
            
            # Process images in batches
            analysis_results = await process_images_in_batch(images_data)
            
            # Add results to final text
            for page_num, analysis_result in analysis_results:
                final_text += f"\n\nImage Analysis (Page {page_num}): {analysis_result}"
                
        except Exception as e:
            logger.error(f"Failed to process PDF images: {e}")
    
    logger.info(f"Preview of cleaned text and images (first 500 chars): {final_text[:500]}")
    return {"text_and_image_analysis": final_text.strip()}

async def process_docx(docx_file: UploadFile):
    """
    Process a DOCX file with batch image processing.
    """
    docx_bytes = await docx_file.read()
    docx_stream = BytesIO(docx_bytes)
    document = Document(docx_stream)
    final_text = ""

    # Process text
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            cleaned_text = re.sub(r'\s+', ' ', text)
            final_text += f" {cleaned_text}"

    # Prepare images for batch processing
    images_data = []
    for idx, rel in enumerate(document.part.rels.values()):
        if isinstance(rel.target_part, ImagePart):
            try:
                images_data.append((idx, rel.target_part.blob))
            except Exception as e:
                logger.error(f"Failed to extract DOCX image {idx}: {e}")

    # Process images in batches
    if images_data:
        analysis_results = await process_images_in_batch(images_data)
        for idx, analysis_result in analysis_results:
            final_text += f"\n\nImage Analysis (Image {idx + 1}): {analysis_result}"

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



async def process_initial_agents(thesis_text: str) -> Dict[str, str]:
    """
    Process the initial set of agents concurrently in a batch.
    
    Args:
        thesis_text: The thesis text to analyze
        
    Returns:
        Dictionary containing results from all initial agents
    """
    # Create tasks for initial agents
    tasks = [
        extract_degree_agent(thesis_text),
        extract_name_agent(thesis_text),
        extract_topic_agent(thesis_text)
    ]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and handle any errors
    degree, name, topic = None, None, None
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Initial agent {i} failed with error: {result}")
            continue
            
        # Assign results based on index
        if i == 0:
            degree = result
        elif i == 1:
            name = result
        elif i == 2:
            topic = result
    
    return {
        "degree": degree or "Not found",
        "name": name or "Not found",
        "topic": topic or "Not found"
    }

###################################################HELPER FUNCTIONS###################################################
###################################################HELPER FUNCTIONS###################################################
###################################################HELPER FUNCTIONS###################################################


def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)

if __name__ == "__main__":
    main()