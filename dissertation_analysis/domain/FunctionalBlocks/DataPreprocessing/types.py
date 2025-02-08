from pydantic import BaseModel
from typing import List, Dict, Tuple, Optional # Pydantic models for request/response validation

# Pydantic models for request/response validation
class ChunkTextResponse(BaseModel):
    chunks: List[Tuple[str, int]]

class TextChunkRequest(BaseModel):
    text: str
    chunk_size: Optional[int] = 1000

class FirstWordsRequest(BaseModel):
    text: str
    n_words: int

class FirstWordsResponse(BaseModel):
    text: str

class ImageProcessingResponse(BaseModel):
    analysis_results: Dict[int, str]

class DocumentAnalysisResponse(BaseModel):
    text_and_image_analysis: str
