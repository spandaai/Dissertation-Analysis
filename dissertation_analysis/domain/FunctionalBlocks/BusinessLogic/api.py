from fastapi import FastAPI, HTTPException
from typing import List
import logging
import uvicorn

from dissertation_analysis.domain.FunctionalBlocks.BusinessLogic.types import *
from dissertation_analysis.domain.FunctionalBlocks.BusinessLogic.business_logic import summarize_and_analyze_agent, process_initial_agents, process_chunks_in_batch, scoring_agent, extract_degree_agent, extract_name_agent, extract_topic_agent

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dissertation Analysis API",
             description="API for analyzing and processing dissertations",
             version="1.0.0")


@app.post("/api/process-chunks", response_model=List[str])
async def process_chunks_endpoint(request: ProcessChunksRequest):
    """
    Process text chunks in batches for summarization.
    """
    try:
        results = await process_chunks_in_batch(
            chunks=request.chunks,
            system_prompt=request.system_prompt,
            batch_size=request.batch_size
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/summarize-analyze", response_model=SummaryResponse)
async def summarize_analyze_endpoint(request: ThesisText):
    """
    Summarize and analyze a thesis document.
    """
    try:
        summary = await summarize_and_analyze_agent(request.text)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract-name", response_model=dict)
async def extract_name_endpoint(request: ThesisText):
    """
    Extract author name from dissertation.
    """
    try:
        name = await extract_name_agent(request.text)
        return {"name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract-topic", response_model=dict)
async def extract_topic_endpoint(request: ThesisText):
    """
    Extract topic from dissertation.
    """
    try:
        topic = await extract_topic_agent(request.text)
        return {"topic": topic}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract-degree", response_model=dict)
async def extract_degree_endpoint(request: ThesisText):
    """
    Extract degree information from dissertation.
    """
    try:
        degree = await extract_degree_agent(request.text)
        return {"degree": degree}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scoring", response_model=ScoringResponse)
async def scoring_endpoint(request: ScoringRequest):
    """
    Score a dissertation based on provided criteria.
    """
    try:
        score = await scoring_agent(
            analysis=request.analysis,
            criteria=request.criteria,
            score_guidelines=request.score_guidelines,
            criteria_guidelines=request.criteria_guidelines,
            feedback=request.feedback
        )
        return {"score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-initial", response_model=InitialAnalysisResponse)
async def process_initial_endpoint(request: ThesisText):
    """
    Process initial analysis of dissertation including name, topic, and degree extraction.
    """
    try:
        results = await process_initial_agents(request.text)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Main function to start the FastAPI server
def main():
    uvicorn.run(app, host="0.0.0.0", port=9002)


if __name__ == "__main__":
    main()
