"""
Text Chunking Utility Module

A simple utility module that provides functions for chunking and word extraction 
from text using LangChain's recursive splitter.
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
   
Functions:
1. chunk_text:
  - Splits text into semantic chunks
  - Uses LangChain's RecursiveCharacterTextSplitter
  - Returns chunks with word counts
  - Configurable chunk size

2. get_first_n_words:
  - Extracts first N words from text
  - Simple space-based word splitting
  - Returns concatenated string

Dependencies:
- langchain_text_splitters: For RecursiveCharacterTextSplitter

Note: This is a utility module focused solely on text chunking and word 
extraction operations. Used primarily for preprocessing text before analysis.
"""
import os
import base64
import logging
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")
vllm_url = os.getenv("VLLM_URL_FOR_ANALYSIS")


def chunk_text(text, chunk_size=1000):
    """
    Splits text into semantic chunks using LangChain's RecursiveCharacterTextSplitter,
    maintaining similar output format as the original function.
    
    Args:
        text (str): The input text to be chunked
        chunk_size (int): Target size for each chunk in words (approximate)
        
    Returns:
        list: List of tuples (chunk_text, actual_chunk_size)
    """
    # Initialize the text splitter
    # Using average word length of 5 characters + 1 for space to convert words to chars
    chars_per_chunk = chunk_size * 6
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chars_per_chunk,
        chunk_overlap=0,  # Some overlap to maintain context
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    # Split the text
    raw_chunks = text_splitter.split_text(text)
    
    # Convert to required format with word counts
    chunks = []
    for chunk in raw_chunks:
        word_count = len(chunk.split())
        chunks.append((chunk, word_count))
    
    return chunks

def get_first_n_words(text, n):
    # Split the text into words
    words = text.split()
    # Get the first 500 words
    first_n_words = words[:n]
    # Join them back into a string
    return " ".join(first_n_words)



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
