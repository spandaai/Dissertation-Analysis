from backend.Agents.agent_utils import chunk_text, get_first_n_words
from backend.InferenceEngine.inference_engines import invoke_llm, ModelType

import asyncio
from dotenv import load_dotenv
import logging
import os
from typing import List


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
ollama_url = os.getenv("OLLAMA_URL")

vllm_url_for_summary = os.getenv("VLLM_URL_FOR_SUMMARY")
vllm_url_for_analysis = os.getenv("VLLM_URL_FOR_ANALYSIS")
vllm_url_for_scoring = os.getenv("VLLM_URL_FOR_SCORING")
vllm_url_for_extraction = os.getenv("VLLM_URL_FOR_EXTRACTION")


async def process_chunks_in_batch(chunks: List[str], topic: str, system_prompt: str, batch_size: int = 5) -> List[str]:
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
## Context
Topic: {topic}

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

async def summarize_and_analyze_agent(thesis: str, topic: str) -> str:
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
- Distill complex research into clear summary
- Capture key elements: 
  - Research question
  - Methodology
  - Key findings
  - Academic significance

## Summary Structure
1. Research context
2. Central research question
3. Methodology overview
4. Primary discoveries
5. Research implications

## Principles
- Use academic language
- Maintain objectivity
    """
    
    # Split text into chunks
    chunks = chunk_text(thesis, chunk_size=1000)
    
    # Process chunks in batches
    summarized_chunks = await process_chunks_in_batch(
        chunks=chunks,
        topic=topic,
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


async def extract_scope_agent(dissertation):
    
    dissertation_first_pages = get_first_n_words(dissertation, -1)

    extract_scope_system_prompt = """
You are an academic expert tasked with identifying the scope of a dissertation. Your job is to clearly indicate the scope of the dissertation that the student is working on.
"""

    # Prompt to extract main topic
    extract_scope_user_prompt = f"""
# Scope Extraction
## Input
The text contains the first few pages of a dissertation:

[CHUNK STARTS]
{dissertation_first_pages}
[CHUNK ENDS]

## Instructions
- Extract the complete scope of the dissertation
- Return ONLY the scope
- Do not include any additional explanation or comments
- Only extract and send the scope, nothing else.

## Output Format
Scope should be returned in a list format. If there is no scope inferred, please return exactly the following:
"no_scope_inferred"
"""

    # Generate the response using the utility function
    full_text_dict = await invoke_llm(
        system_prompt=extract_scope_system_prompt,
        user_prompt=extract_scope_user_prompt,
        model_type=ModelType.EXTRACTION
    )

    topic = full_text_dict["answer"]
    
    return topic 

async def scoped_suggestions_agent(dissertation_scores, scope):

    scoped_suggestions_system_prompt = """
You are a highly precise academic dissertation advisor. Your task is to extract only the most specific and actionable suggestions from dissertation feedback. Focus exclusively on concrete, implementable changes rather than general advice.

Respond only with the numbered list of 3-4 specific action items as requested. Do not provide explanations, analysis, or any additional text beyond the requested list.

Only include suggestions that:
1. Are explicitly mentioned in the feedback
2. Can be directly implemented without further clarification
3. Target specific sections or elements of the dissertation
4. Are within the stated scope of the work

Maintain academic rigor and specificity in your extracted suggestions.
"""

    scoped_feedback = dict()
    for key in dissertation_scores['criteria_evaluations']:
        # Prompt to extract main topic
        scoped_suggestions_user_prompt = f"""
# Key Suggestion Extraction
## Input
The text contains feedback on the dissertation:
[CHUNK STARTS]
{dissertation_scores['criteria_evaluations'][key]}
[CHUNK ENDS]

This text contains the scope of the dissertation:
[CHUNK STARTS]
{scope}
[CHUNK ENDS]

## Instructions
- Extract exactly 3-4 important suggestions that ALREADY EXIST in the feedback text
- DO NOT create new suggestions or modify the existing ones
- Selection criteria:
  1. Choose meaningful suggestions that address substantive issues
  2. Prioritize suggestions that are within the dissertation's scope
  3. Select suggestions that would have the highest impact on improving the work
  4. Avoid overly prescriptive instructions (like "add a section here")
- The original feedback contains many points - your task is to identify only the 3-4 most important ones

## Output Format
Return only a numbered list of 3-4 key suggestions extracted from the original feedback.
"""

        # Generate the response using the utility function
        full_text_dict = await invoke_llm(
            system_prompt=scoped_suggestions_system_prompt,
            user_prompt=scoped_suggestions_user_prompt,
            model_type=ModelType.EXTRACTION
        )

        scoped_feedback[key] = full_text_dict["answer"]
    
    return scoped_feedback