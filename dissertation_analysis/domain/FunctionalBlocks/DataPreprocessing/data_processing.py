import os
import logging
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
from langchain_text_splitters import RecursiveCharacterTextSplitter
import asyncio
import fitz
import re
from docx import Document
from docx.parts.image import ImagePart
from fastapi import UploadFile
from typing import List, Dict, Tuple

from dissertation_analysis.platform.service_client import analyze_image

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


async def process_images_in_batch(
    images_data: List[Tuple[int, bytes]],
    batch_size: int = 5
) -> Dict[int, str]:
    """
    Process images in batches, resizing each image and sending them concurrently.
    Includes additional error handling and validation.

    Args:
        images_data: List of tuples containing (page_or_image_number, image_bytes)
        batch_size: Number of images to process in each batch

    Returns:
        Dictionary mapping page/image number to analysis result
    """
    ordered_results = {}

    for i in range(0, len(images_data), batch_size):
        batch = images_data[i:i + batch_size]

        try:
            # Resize images in the batch with minimum size requirement
            resized_batch = []
            for page_num, img_bytes in batch:
                try:
                    resized_img = resize_image(img_bytes, max_size=800, min_size=70)
                    resized_batch.append((page_num, resized_img))
                except Exception as e:
                    logger.error(f"Failed to resize image at page {page_num}: {e}")
                    continue

            # Skip batch if no images were successfully resized
            if not resized_batch:
                continue

            # Create async tasks for image analysis
            batch_tasks = [
                asyncio.create_task(analyze_image(img_bytes))
                for _, img_bytes in resized_batch
            ]

            # Run all tasks in the current batch concurrently
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Process results
            for (page_num, _), result in zip(resized_batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to analyze image at page {page_num}: {result}")
                    continue
                
                if isinstance(result, dict) and 'response' in result:
                    analysis_result = result['response'].strip()
                    if analysis_result:
                        ordered_results[page_num] = analysis_result

        except Exception as e:
            logger.error(f"Failed to process batch starting at index {i}: {e}")
            continue

    return dict(sorted(ordered_results.items()))



async def process_pdf(pdf_file: UploadFile) -> Dict[str, str]:
    """
    Process PDF file extracting text and images while preserving their original sequence.
    
    Args:
        pdf_file: Uploaded PDF file
    
    Returns:
        Dictionary with extracted text and image analyses in original sequence
    """
    pdf_bytes = await pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # Use a list to maintain order instead of OrderedDict
    final_elements = []
    images_data = []

    # Start image analysis from page 7
    image_analysis_start_page = 6  # Pages are zero-indexed, so page 7 is index 6

    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # Extract text using custom method for better block extraction
        page_text = extract_and_clean_text_from_page(page)
        if page_text:
            final_elements.append((page_num + 1, 'text', page_text))
        
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
    image_analyses = await process_images_in_batch(images_data) if images_data else {}
    
    # Insert image analyses into the final_elements list in their original positions
    for page_num, analysis in image_analyses.items():
        # Find the index where we want to insert the image analysis
        insert_index = next(
            (i for i, (p, type_, _) in enumerate(final_elements) 
             if p == page_num and type_ == 'text'), 
            len(final_elements)
        )
        
        # Insert image analysis right after the corresponding text
        final_elements.insert(insert_index + 1, (page_num, 'image', analysis))

    doc.close()
    
    # Combine text and image analyses in order
    combined_text = []
    for page_num, content_type, content in final_elements:
        if content_type == 'text':
            combined_text.append(content)
        else:  # image
            combined_text.append(f"\n[Image Analysis on Page {page_num}]: {content}")

    return {"text_and_image_analysis": "\n".join(combined_text).strip()}

async def process_docx(docx_file: UploadFile):
    """
    Process a DOCX file with batch image processing, handling both embedded and external images.
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
        try:
            # Check if the relationship is an image and is embedded (not external)
            if (isinstance(rel.target_part, ImagePart) and 
                hasattr(rel.target_part, 'blob') and 
                rel.target_mode != 'External'):
                try:
                    images_data.append((idx, rel.target_part.blob))
                except Exception as img_e:
                    logger.error(f"Failed to extract embedded image {idx}: {img_e}")
            elif hasattr(rel, 'target_mode') and rel.target_mode == 'External':
                # Log external image reference but don't try to process it
                logger.info(f"Skipping external image reference at index {idx}")
        except Exception as e:
            logger.error(f"Failed to process relationship {idx}: {e}")
            continue

    # Process images in batches
    if images_data:
        analysis_results = await process_images_in_batch(images_data)

        # Add results to final text
        for idx, analysis_result in sorted(analysis_results.items()):
            final_text += f"\n\nImage Analysis (Image {idx + 1}): {analysis_result}"
            
    cleaned_text = clean_text(final_text)
    return {"text_and_image_analysis": cleaned_text.strip()}

