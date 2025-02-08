import asyncio
import logging
from dotenv import load_dotenv
from dissertation_analysis.common.configs import ModelType
from dissertation_analysis.platform.service_client import invoke_llm
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from typing import List, Dict


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
