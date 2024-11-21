from backend.src.utils import *
from backend.src.image_agents import *
import uvicorn
from backend.src.agents import *
from backend.src.dissertation_types import QueryRequestThesisAndRubric, QueryRequestThesis,UserData,UserScoreData,PostData,FeedbackData ,User, UserScore, Feedback
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException ,Depends
from fastapi.middleware.cors import CORSMiddleware 
import re
import fitz
import logging
from io import BytesIO
from docx import Document
from docx.parts.image import ImagePart
from PIL import Image
from typing import Dict, Tuple
import asyncio
from collections import OrderedDict
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

load_dotenv()

# Get the database URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")


engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  


def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
init_db()
# Create FastAPI app instance
app = FastAPI(
    title="Dissertation Analysis API",
    description="API for analyzing dissertations",
    version="1.0.0"
)
origins = [
    "http://localhost",
    "http://localhost:4000",

]
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



@app.post("/api/postUserData")
def post_user_data(postData: PostData, db: Session = Depends(get_db)):
    # Check if user exists based on unique combination of name, degree, and topic
    db_user = db.query(User).filter_by(
        name=postData.userData.name,
        degree=postData.userData.degree,
        topic=postData.userData.topic
    ).first()

    if db_user:
        # Update user total score
        db_user.total_score = postData.userData.total_score
    else:
        # Insert new user data if not exists
        db_user = User(
            name=postData.userData.name,
            degree=postData.userData.degree,
            topic=postData.userData.topic,
            total_score=postData.userData.total_score
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    # Update or insert user score data
    existing_scores = {score.dimension_name: score for score in db_user.scores}
    
    for score_data in postData.userScores:
        if score_data.dimension_name in existing_scores:
            # Update existing score
            existing_scores[score_data.dimension_name].score = score_data.score
        else:
            # Insert new score
            db_score = UserScore(
                user_id=db_user.id,
                dimension_name=score_data.dimension_name,
                score=score_data.score
            )
            db.add(db_score)
    
    db.commit()

    return {"message": "Data successfully stored", "user_id": db_user.id}


@app.post("/api/submitFeedback")
def submit_feedback(feedback_data: FeedbackData, db: Session = Depends(get_db)):
    # Insert the feedback into the database
    feedback_entry = Feedback(
        selected_text=feedback_data.selectedText,
        feedback=feedback_data.feedback
    )
    db.add(feedback_entry)
    db.commit()
    db.refresh(feedback_entry)

    return {"message": "Feedback stored successfully", "feedback_id": feedback_entry.id}


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
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")            
            # print(dissertation_system_prompt)
            # print(dissertation_user_prompt)
            # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
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
def resize_image(image_bytes: bytes, max_size: int = 800) -> bytes:
    """
    Resize an image to ensure both dimensions are smaller than max_size while maintaining the aspect ratio.
    If the image dimensions are already smaller than max_size, it will not be resized.
    
    Args:
        image_bytes: Original image bytes.
        max_size: Maximum allowed size for any dimension.

    Returns:
        Resized image bytes (or original if no resizing is needed).
    """
    with Image.open(BytesIO(image_bytes)) as img:
        # Check if resizing is needed
        if img.width > max_size or img.height > max_size:
            # Resize the image while maintaining the aspect ratio
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Save the resized image into a BytesIO object
        output = BytesIO()
        img.save(output, format=img.format)  # Preserve original format
        return output.getvalue()


async def process_images_in_batch(
    images_data: List[Tuple[int, bytes]],
    batch_size: int = 10
) -> Dict[int, str]:
    """
    Process images in batches, resizing each image and sending them concurrently while preserving the order.

    Args:
        images_data: List of tuples containing (page_or_image_number, image_bytes).
        batch_size: Number of images to process in each batch.

    Returns:
        Dictionary mapping page/image number to analysis result.
    """
    ordered_results = {}  # Dictionary to preserve results by image number

    for i in range(0, len(images_data), batch_size):
        batch = images_data[i:i + batch_size]  # Get the current batch of images

        # Resize images in the batch
        resized_batch = [
            (page_num, resize_image(img_bytes, max_size=800))
            for page_num, img_bytes in batch
        ]

        # Create async tasks for image analysis
        batch_tasks = [
            asyncio.create_task(analyze_image(img_bytes))
            for page_num, img_bytes in resized_batch
        ]

        # Run all tasks in the current batch concurrently
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        # Pair results with their respective page/image numbers
        for (page_num, _), result in zip(batch, batch_results):
            if isinstance(result, Exception):
                # Log or handle the exception as needed
                print(f"Failed to analyze image at {page_num}: {result}")
                continue
            # Process valid results
            if isinstance(result, dict) and 'response' in result:
                analysis_result = result['response'].strip()
                if analysis_result:  # Only include valid, non-empty responses
                    ordered_results[page_num] = analysis_result

    # Return results sorted by page/image number
    return dict(sorted(ordered_results.items()))



async def process_pdf(pdf_file: UploadFile) -> Dict[str, str]:
    """
    Process PDF file extracting text and images using PyMuPDF.
    
    Args:
        pdf_file: Uploaded PDF file
    
    Returns:
        Dictionary with extracted text and image analyses
    """
    pdf_bytes = await pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    final_elements = OrderedDict()
    images_data = []

    # Start image analysis from page 7
    image_analysis_start_page = 6  # Pages are zero-indexed, so page 7 is index 6

    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # Extract text using custom method for better block extraction
        page_text = extract_and_clean_text_from_page(page)
        if page_text:
            final_elements[(page_num + 1, 'text')] = page_text
        
        # Extract images from page, only analyze images starting from page 7
        if page_num >= image_analysis_start_page:
            for img_index, img in enumerate(page.get_images(full=True)):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    images_data.append((page_num + 1, image_bytes))
                except Exception as e:
                    logger.error(f"Failed to extract image on page {page_num + 1}: {e}")

    # Process images in batches
    image_analyses = await process_images_in_batch(images_data) if images_data else OrderedDict()
    
    # Combine text with image analyses
    for page_num, analysis in image_analyses.items():
        if (page_num, 'text') in final_elements:
            final_elements[(page_num, 'image')] = analysis
        else:
            final_elements[(page_num, 'image')] = analysis

    doc.close()
    
    combined_text = []
    for key, value in final_elements.items():
        if key[1] == 'text':
            combined_text.append(value)
        else:
            combined_text.append(f"\n[Image Analysis on Page {key[0]}]: {value}")

    return {"text_and_image_analysis": "\n".join(combined_text).strip()}


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

        # Add results to final text
        for idx, analysis_result in sorted(analysis_results.items()):
            final_text += f"\n\nImage Analysis (Image {idx + 1}): {analysis_result}"
            
    cleaned_text = clean_text(final_text)
    return {"text_and_image_analysis": cleaned_text.strip()}


def extract_and_clean_text_from_page(page) -> str:
    """
    Extract and clean text from a PDF page using PyMuPDF.
    
    Args:
        page: PyMuPDF page object
    
    Returns:
        Cleaned text string
    """
    text_blocks = []
    blocks = page.get_text("blocks")
    for block in blocks:
        if isinstance(block[4], str) and block[4].strip():
            cleaned_block = ' '.join(block[4].split())
            if cleaned_block:
                text_blocks.append(cleaned_block)

    combined_text = ' '.join(text_blocks)
    return clean_text(combined_text)

def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing unnecessary elements.
    
    Args:
        text: Input text to clean
    
    Returns:
        Cleaned text string
    """
    import re
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