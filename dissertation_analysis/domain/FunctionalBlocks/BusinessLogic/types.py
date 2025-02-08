from pydantic import BaseModel
from typing import List

# Request/Response Models
class ThesisText(BaseModel):
    text: str

class ProcessChunksRequest(BaseModel):
    chunks: List[str]
    system_prompt: str
    batch_size: int = 5

class ScoringRequest(BaseModel):
    analysis: str
    criteria: str
    score_guidelines: str
    criteria_guidelines: str
    feedback: str

class InitialAnalysisResponse(BaseModel):
    degree: str
    name: str
    topic: str

class ChunkResponse(BaseModel):
    chunks: List[tuple[str, int]]

class SummaryResponse(BaseModel):
    summary: str

class ScoringResponse(BaseModel):
    score: str