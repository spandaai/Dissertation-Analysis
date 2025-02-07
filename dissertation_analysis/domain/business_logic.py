"""
Dissertation Analysis Business Logic
===========================

This module provides a comprehensive system for analyzing academic dissertations using various AI models
and services (VLLM and Ollama). It includes functionality for image analysis, text summarization,
metadata extraction, and dissertation scoring.

Key Components:
--------------
1. Image Analysis
    - Supports both VLLM and OLLAMA backends
    - Provides unified interface for image analysis
    - Falls back to alternative service if primary is unavailable

2. Text Processing
    - Chunks large texts for efficient processing
    - Processes chunks in parallel using batching
    - Maintains academic context during analysis

3. Metadata Extraction
    - Extracts author name from dissertation
    - Identifies dissertation topic
    - Determines degree being pursued

4. Scoring System
    - Evaluates dissertations based on specific criteria
    - Uses expert feedback for scoring
    - Provides numerical scores on a 0-5 scale

5. Summarization
    - Creates concise summaries of dissertation content
    - Maintains academic tone and precision
    - Focuses on key research elements


Note: All main functions are asynchronous and should be run within an async context.
"""

import asyncio
import fitz
import re
import logging
from dotenv import load_dotenv
from io import BytesIO
from docx import Document
from docx.parts.image import ImagePart
from fastapi import UploadFile
from dotenv import load_dotenv
from dissertation_analysis.common.configs import ModelType
from dissertation_analysis.domain.data_preprocessing import get_first_n_words, chunk_text, clean_text, extract_and_clean_text_from_page, resize_image
from dissertation_analysis.domain.inference_client import generate_from_image, generate_from_image_ollama
from dissertation_analysis.platform.service_client import invoke_llm
import logging
import asyncio
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple
import logging


# Load environment variables from .env file
load_dotenv()

vllm_url_for_summary = os.getenv("VLLM_URL_FOR_SUMMARY")
vllm_url_for_analysis = os.getenv("VLLM_URL_FOR_ANALYSIS")
vllm_url_for_scoring = os.getenv("VLLM_URL_FOR_SCORING")
vllm_url_for_extraction = os.getenv("VLLM_URL_FOR_EXTRACTION")

vllm_url_for_image = os.getenv("VLLM_URL_FOR_IMAGE")
vllm_model_for_image = os.getenv("VLLM_MODEL_FOR_IMAGE")

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")
ollama_model_for_image = os.getenv("OLLAMA_MODEL_FOR_IMAGE")


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


# choose agent
async def analyze_image(image_data: bytes) -> Dict[str, Any]:
    """
    Unified method to analyze images using either VLLM or Ollama based on available environment variables.
    VLLM takes precedence if both are configured.
    
    Args:
        image_data: Image bytes to analyze
        
    Returns:
        Dict containing the analysis response
    
    Raises:
        ValueError: If neither VLLM nor Ollama environment variables are configured
    """
    # Check VLLM configuration
    has_vllm = all([
        vllm_url_for_image,
        vllm_model_for_image
    ])
    
    # Check Ollama configuration
    has_ollama = all([
        ollama_url,
        ollama_model_for_image
    ])
    
    # If neither service is configured, raise error
    if not (has_vllm or has_ollama):
        raise ValueError(
            "No image analysis service configured. Please set either VLLM "
            "(VLLM_URL_FOR_IMAGE, VLLM_MODEL_FOR_IMAGE) or Ollama "
            "(OLLAMA_URL, OLLAMA_MODEL_FOR_IMAGE) environment variables."
        )
    
    try:
        # Prefer VLLM if available
        if has_vllm:
            logger.info("Using VLLM for image analysis")
            return await analyze_image_vllm(image_data)
        else:
            logger.info("Using Ollama for image analysis")
            return await analyze_image_ollama(image_data)
            
    except Exception as e:
        logger.error(f"Error in analyze_image: {str(e)}")
        return {"response": f"Failed to analyze image: {str(e)}"}


###############################################################################################################################################################
###############################################################################################################################################################
#########################################VLLM IMAGE AGENT###############################################################################################
###############################################################################################################################################################

async def analyze_image_vllm(
    image_data: bytes,
    model: str = vllm_model_for_image,
    base_url: str = vllm_url_for_image
) -> Dict[str, Any]:
    """
    Analyze image using predefined prompt
    
    Args:
        image_data: Image bytes
        model: Model identifier
        base_url: API base URL
    
    Returns:
        Dict containing the analysis response
    """

    image_agent_user_prompt = """
    Analyze the following image and provide a report detailing the features present. 
    Include a clear description of what is depicted in the image without any interpretation.
    Please keep the summarization below 200 words. Describe the intent of the image, not the details of what is present.
    The summarization needs to be brief and short.
    """
    
    return await generate_from_image(
        image_data=image_data,
        prompt=image_agent_user_prompt,
        model=model,
        base_url=base_url
    )

###############################################################################################################################################################
#########################################OLLAMA IMAGE AGENT####################################################################################################
###############################################################################################################################################################
###############################################################################################################################################################


async def analyze_image_ollama(image_data: bytes):
    image_agent_user_prompt = """
    Analyze the following image and provide a report detailing the features present. 
    Include a clear description of what is depicted in the image without any interpretation.
    Please keep the summarization below 200 words. Describe the intent of the image, not the details of what is present.
    The summarization needs to be brief and short.
    """
    return await generate_from_image_ollama(image_data, image_agent_user_prompt)



async def process_chunks_in_batch(chunks: List[str], system_prompt: str, batch_size: int = 5) -> List[str]:
    """
    Process text chunks in batches for summarization.
    
    Args:
        chunks: List of text chunks to summarize
        topic: The thesis topic for context
        system_prompt: The system prompt for the LLM
        batch_size: Number of chunks to process in each batch
        
    Returns:
        List of summarized chunks
    """
    summarized_chunks = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_tasks = []
        
        # Create tasks for each chunk in the batch
        for chunk in batch:
            user_prompt = f'''
# Input Content
## Dissertation Segment
{chunk[0]}

# Summarization Instructions
1. Extract the most critical elements:
   - Core arguments
   - Key evidence
   - Fundamental insights
   - Primary conclusions

# Summarization Constraints
- Maximum brevity
- Absolute fidelity to source text
- Academic precision
- No external information
- No speculation
- No additional context

# Output Specifications
- Compress to essential informational nucleus
- Preserve logical progression
- Maintain scholarly tone
- Focus on substantive content
- Eliminate redundancies
- Prioritize analytical significance
'''
            # Create coroutine for this chunk
            task = asyncio.create_task(invoke_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_type=ModelType.SUMMARY
            ))
            batch_tasks.append(task)
        
        try:
            # Process batch concurrently
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results and handle any errors
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Failed to summarize chunk: {result}")
                    summarized_chunks.append("")
                else:
                    summarized_chunks.append(result["answer"])
                    print(result["answer"])
                    print("################################################")
                    
        except Exception as e:
            logger.error(f"Failed to process batch: {e}")
            # Add empty strings for the entire failed batch
            summarized_chunks.extend([""] * len(batch_tasks))
    
    return summarized_chunks

async def summarize_and_analyze_agent(thesis: str) -> str:
    """
    Summarize and analyze a thesis document.
    
    Args:
        thesis: The full thesis text
        topic: The thesis topic
        
    Returns:
        A final summary of the thesis
    """
    summarize_system_prompt = """
# Dissertation Summarization System

## Objectives
- Distill complex research into clear summary paragraph
- Capture key elements: 
  - Research question
  - Methodology
  - Key findings
  - Academic significance

## Principles
- Use academic language
- Maintain objectivity
    """
    
    # Split text into chunks
    chunks = chunk_text(thesis, chunk_size=1000)
    
    # Process chunks in batches
    summarized_chunks = await process_chunks_in_batch(
        chunks=chunks,
        system_prompt=summarize_system_prompt,
        batch_size=5
    )
    
    # Combine all summarized chunks into a final summary
    final_summary = " ".join(filter(None, summarized_chunks)).replace("\n", "")
    
    return final_summary

async def extract_name_agent(dissertation):
    
    dissertation_first_pages = get_first_n_words(dissertation, 300)

    extract_name_system_prompt = """
    You are an academic expert tasked with identifying the author of a dissertation. Your job is to find the exact wording or phrase in the text that clearly indicates the author's name.
    Do not interpret, summarize, or infer—only locate and extract the exact name mentioned in the text. Respond with the precise name as it appears in the document.
    """

    extract_name_user_prompt = f"""
# Author Name Extraction
## Input
The text contains the first few pages of a dissertation:

[CHUNK STARTS]
{dissertation_first_pages}
[CHUNK ENDS]

## Instructions
- Extract the exact wording or phrase that clearly states the author's name
- Return ONLY the exact name as mentioned in the text
- Do not include any additional explanation or comments
- Only extract and send the name, nothing else.

## Output Format
Name should be returned exactly as written in the text. If there is no name available, please return exactly the following:
"no_name_found"
"""
        
        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_name_system_prompt,
        user_prompt=extract_name_user_prompt,
        model_type=ModelType.EXTRACTION
    )

    name = full_text_dict["answer"]
    print("THE NAME IS IS: " + name)
    # Final response with aggregated feedback and score
    
    return name 


async def extract_topic_agent(dissertation):
    
    dissertation_first_pages = get_first_n_words(dissertation, 300)

    extract_topic_system_prompt = """
You are an academic expert tasked with identifying the main topic of a dissertation. Your job is to find the exact wording or phrase in the text that clearly indicates the primary topic the student is working on.
Do not interpret, summarize, or infer—only locate and extract the exact topic mentioned in the text. Respond with the precise words or phrase that describe the topic.
"""

    # Prompt to extract main topic
    extract_topic_user_prompt = f"""
# Topic Extraction
## Input
The text contains the first few pages of a dissertation:

[CHUNK STARTS]
{dissertation_first_pages}
[CHUNK ENDS]

## Instructions
- Extract the exact wording or phrase that clearly states the main topic
- Return ONLY the exact topic as mentioned in the text
- Do not include any additional explanation or comments
- Only extract and send the topic, nothing else.

## Output Format
Topic should be returned exactly as written in the text. If there is no topic available, please return exactly the following:
"no_topic_found"
"""

        
        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_topic_system_prompt,
        user_prompt=extract_topic_user_prompt,
        model_type=ModelType.EXTRACTION
    )

    topic = full_text_dict["answer"]
    print("THE TOPIC IS: " + topic)
    # Final response with aggregated feedback and score
    
    return topic 


async def extract_degree_agent(dissertation):
    
    dissertation_first_pages = get_first_n_words(dissertation, 300)

    extract_degree_system_prompt = """
You are an academic expert tasked with identifying the degree that the submitter is pursuing in a dissertation. Your job is to find the exact wording or phrase in the text that clearly indicates the degree being pursued by the student.
Do not interpret, summarize, or infer—only locate and extract the exact degree mentioned in the text. Respond with the precise words or phrase that describe the degree.
"""

    extract_degree_user_prompt = f"""
# Degree Information Extraction
## Input
The text contains the first few pages of a dissertation:

[CHUNK STARTS]
{dissertation_first_pages}
[CHUNK ENDS]

## Instructions
- Extract the exact wording or phrase that clearly states the degree being pursued
- Return ONLY the exact degree as mentioned in the text
- Do not include any additional explanation or comments
- Only extract and send the degree, nothing else.

# Output Format
Degree should be returned exactly as written in the text. If there is no degree available, please return exactly the following:
"no_degree_found"
"""

        # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_degree_system_prompt,
        user_prompt=extract_degree_user_prompt,
        model_type=ModelType.EXTRACTION
    )
    
    degree = full_text_dict["answer"]
    print("THE DEGREE IS: " + degree)
    
    return degree 

async def scoring_agent(analysis, criteria, score_guidelines, criteria_guidelines, feedback):
    scoring_agent_system_prompt = """You are a precise scoring agent that evaluates one dissertation criterion at a time. 
    Review the provided criterion analysis, match it to the scoring guidelines, and assign a score from 0 to 5, without justification, solely use the analysis for your justification. 
    Evaluate only the assigned criterion, using only the given analysis, and follow the guidelines exactly. 
    Do not consider external factors, make assumptions, or deviate from objective standards."""

    scoring_agent_user_prompt = f"""# Provide a score for the following analysis done:

-Analysis: {analysis}

-Explanation of {criteria}: {criteria_guidelines}

-Guidelines of scoring for {criteria}: {score_guidelines}

Your score will only be for the following criterion: {criteria}. Provide ONLY the score based on the analysis that has been done. Be very critical while providing the score.

IMPORTANT(The following feedback was provided by an expert. Consider the feedback properly, and ensure your evaluation follows this feedback): {feedback}

Required output format. It is extremely important for the score to be displayed in this exact format with no formatting and whitespaces:
spanda_score: <score (out of 5)>"""
        
    # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=scoring_agent_system_prompt,
        user_prompt=scoring_agent_user_prompt,
        model_type=ModelType.SCORING
    )

    score_for_criteria = full_text_dict["answer"]
    
    return score_for_criteria 



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


