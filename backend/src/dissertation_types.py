from typing import Dict, Optional
from pydantic import BaseModel
from typing_extensions import TypedDict
from pydantic import BaseModel

class RubricCriteria(TypedDict):
    criteria_explanation: str
    score_explanation: str
    criteria_output: str

# Define the structure for the pre-analysis dictionary
class PreAnalysis(BaseModel):
    degree: str
    name: str
    topic: str
    pre_analyzed_summary: str

class QueryRequestThesisAndRubric(BaseModel):
    rubric: Dict[str, RubricCriteria]
    pre_analysis: PreAnalysis
    feedback: Optional[str] = None  # Makes feedback optional

class QueryRequestThesis(BaseModel):
    thesis: str
