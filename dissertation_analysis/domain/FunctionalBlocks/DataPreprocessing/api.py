from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import Response
from typing import List, Optional
import logging
import uvicorn
from dissertation_analysis.domain.FunctionalBlocks.DataPreprocessing.types import *
from dissertation_analysis.domain.FunctionalBlocks.DataPreprocessing.data_processing import (
    chunk_text,
    get_first_n_words,
    resize_image,
    process_pdf,
    process_docx,
    process_images_in_batch
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Data Preprocessing API",
    description="API for text and document preprocessing operations",
    version="1.0.0"
)

@app.post("/api/chunk-text", response_model=ChunkTextResponse)
async def api_chunk_text(request: TextChunkRequest):
    """
    Split text into semantic chunks using LangChain's RecursiveCharacterTextSplitter.
    
    Args:
        text: Input text to be chunked
        chunk_size: Target size for each chunk in words (optional, default=1000)
    
    Returns:
        List of tuples containing (chunk_text, word_count)
    """
    try:
        chunks = chunk_text(request.text, request.chunk_size)
        return ChunkTextResponse(chunks=chunks)
    except Exception as e:
        logger.error(f"Error in chunk_text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/first-n-words", response_model=FirstWordsResponse)
async def api_first_n_words(request: FirstWordsRequest):
    """
    Get the first N words from a text.
    
    Args:
        text: Input text
        n_words: Number of words to extract
    
    Returns:
        First N words as a string
    """
    try:
        result = get_first_n_words(request.text, request.n_words)
        return FirstWordsResponse(text=result)
    except Exception as e:
        logger.error(f"Error in get_first_n_words: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resize-image")
async def api_resize_image(
    file: UploadFile,
    max_size: Optional[int] = 800,
    min_size: Optional[int] = 70
):
    """
    Resize an uploaded image while maintaining aspect ratio.
    
    Args:
        file: Uploaded image file
        max_size: Maximum allowed dimension
        min_size: Minimum allowed dimension
    
    Returns:
        Resized image bytes
    """
    try:
        image_bytes = await file.read()
        resized_image = resize_image(image_bytes, max_size, min_size)
        return Response(
            content=resized_image,
            media_type=file.content_type or "application/octet-stream"
        )
    except Exception as e:
        logger.error(f"Error in resize_image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-images-batch", response_model=ImageProcessingResponse)
async def api_process_images_batch(
    files: List[UploadFile],
    batch_size: Optional[int] = 5
):
    """
    Process multiple images in batches for analysis.
    
    Args:
        files: List of image files
        batch_size: Number of images to process in each batch
    
    Returns:
        Dictionary mapping image index to analysis result
    """
    try:
        images_data = []
        for idx, file in enumerate(files):
            image_bytes = await file.read()
            images_data.append((idx, image_bytes))
        
        results = await process_images_in_batch(images_data, batch_size)
        return ImageProcessingResponse(analysis_results=results)
    except Exception as e:
        logger.error(f"Error in process_images_batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-pdf", response_model=DocumentAnalysisResponse)
async def api_process_pdf(file: UploadFile):
    """
    Process a PDF file, extracting text and analyzing images.
    
    Args:
        file: Uploaded PDF file
    
    Returns:
        Combined text and image analysis results
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        result = await process_pdf(file)
        return DocumentAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Error in process_pdf: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-docx", response_model=DocumentAnalysisResponse)
async def api_process_docx(file: UploadFile):
    """
    Process a DOCX file, extracting text and analyzing images.
    
    Args:
        file: Uploaded DOCX file
    
    Returns:
        Combined text and image analysis results
    """
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="File must be a DOCX")
    
    try:
        result = await process_docx(file)
        return DocumentAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Error in process_docx: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}

# Main function to start the FastAPI server
def main():
    uvicorn.run(app, host="0.0.0.0", port=9001)

if __name__ == "__main__":
    main()
