"""
This module contains the utilities that handles the processing and analysis of dissertation documents (PDF and DOCX) 
with comprehensive image and text extraction capabilities.

Key Components:
- PDF and DOCX document processing with text extraction and image analysis
- Asynchronous batch processing of images
- WebSocket simulation for real-time communication
- Environment variable configuration for various services (VLLM, Ollama)
- Robust error handling and logging

Main Features:
1. Document Processing:
   - PDF processing with PyMuPDF (fitz)
   - DOCX processing with python-docx
   - Text extraction and cleaning
   - Image extraction and analysis

2. Image Processing:
   - Base64 encoding of images
   - Image resizing with size constraints
   - Batch processing of images
   - Concurrent image analysis

3. Dissertation Analysis:
   - Extraction of degree information
   - Extraction of author name
   - Extraction of dissertation topic
   - Concurrent processing of analysis agents

4. WebSocket Simulation:
   - Simulated WebSocket class for testing
   - Support for real WebSocket forwarding
   - Queue-based message handling
   - Connection state management

Dependencies:
- asyncio: For asynchronous operations
- fitz (PyMuPDF): For PDF processing
- python-docx: For DOCX processing
- Pillow: For image processing
- FastAPI: For handling file uploads
- python-dotenv: For environment variable management

Environment Variables Required:
- VLLM_URL_FOR_IMAGE
- VLLM_MODEL_FOR_IMAGE
- OLLAMA_URL
- VLLM_URL_FOR_ANALYSIS

Note: This module is designed to work with a larger dissertation analysis system
and requires proper configuration of external services (VLLM, Ollama) to function correctly.
"""

import os
import base64
import logging
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")
vllm_url = os.getenv("VLLM_URL_FOR_ANALYSIS")


async def encode_bytes_to_base64(image_bytes: bytes) -> str:
    """
    Encode image bytes to base64 string.
    
    Args:
        image_bytes: Image data as bytes
    
    Returns:
        Base64 encoded string of the image
    """
    try:
        return base64.b64encode(image_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image: {str(e)}")
        raise


def resize_image(image_bytes: bytes, max_size: int = 800, min_size: int = 70) -> bytes:
    """
    Resize an image to ensure dimensions are between min_size and max_size while maintaining aspect ratio.
    
    Args:
        image_bytes: Original image bytes
        max_size: Maximum allowed size for any dimension
        min_size: Minimum allowed size for any dimension

    Returns:
        Resized image bytes
    """
    with Image.open(BytesIO(image_bytes)) as img:
        # Get original dimensions
        orig_width, orig_height = img.size
        
        # Calculate aspect ratio
        aspect_ratio = orig_width / orig_height

        # Check if image needs to be resized up or down
        needs_upscaling = orig_width < min_size or orig_height < min_size
        needs_downscaling = orig_width > max_size or orig_height > max_size

        if needs_upscaling:
            # If width is smaller than minimum, scale up maintaining aspect ratio
            if orig_width < min_size:
                new_width = min_size
                new_height = int(new_width / aspect_ratio)
                # If height is still too small, scale based on height instead
                if new_height < min_size:
                    new_height = min_size
                    new_width = int(new_height * aspect_ratio)
            else:
                new_height = min_size
                new_width = int(new_height * aspect_ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        elif needs_downscaling:
            # Use thumbnail for downscaling as it preserves aspect ratio
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Save the resized image
        output = BytesIO()
        img.save(output, format=img.format or 'PNG')  # Use PNG as fallback format
        return output.getvalue()


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
