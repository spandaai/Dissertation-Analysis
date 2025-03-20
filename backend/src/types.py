from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint,JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    degree = Column(String(255))
    topic = Column(Text)  
    total_score = Column(Integer)
    evaluator = Column(String(255), index=True)

    scores = relationship("UserScore", back_populates="user")

    __table_args__ = (
        UniqueConstraint('name', 'degree', 'topic', name='unique_user'),  
    )

class UserScore(Base):
    __tablename__ = 'UserScores'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('Users.id'))
    dimension_name = Column(String(255))
    score = Column(Integer)
    data = Column(Text)  


    user = relationship("User", back_populates="scores")

class Feedback(Base):
    __tablename__ = 'Feedbacks'
    id = Column(Integer, primary_key=True, index=True)
    selected_text = Column(Text, nullable=False)  
    feedback = Column(Text, nullable=False)
    pre_analysis=Column(Text, nullable=False)
    

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

class QueryScope(BaseModel):
    feedback: dict
    scope: str

class UserData(BaseModel):
    name: str
    degree: str
    topic: str
    total_score: float

class UserScoreData(BaseModel):
    dimension_name: str
    score: float
    data:str

class PostData(BaseModel):
    userData: UserData
    userScores: List[UserScoreData]

class FeedbackData(BaseModel):
    selectedText: str
    feedback: str
    preAnalysisData: str

class Rubric(Base):
    __tablename__ = "rubrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    dimensions = Column(JSON, nullable=False, default=list)

# Pydantic Models for API
class ScoreExplanationDetail(BaseModel):
    Description: str
    Examples: str
    Explanation: str

class ScoreExplanation(BaseModel):
    Score_1: ScoreExplanationDetail
    Score_2: ScoreExplanationDetail
    Score_3: ScoreExplanationDetail
    Score_4: ScoreExplanationDetail
    Score_5: ScoreExplanationDetail

    class Config:
        arbitrary_types_allowed = True

class Dimension(BaseModel):
    name: str
    criteria_explanation: str
    criteria_output: Dict[str, str]
    score_explanation: Dict[str, Dict[str, str]]

class RubricCreate(BaseModel):
    name: str
    dimensions: List[Dimension]

class RubricUpdate(BaseModel):
    name: str
    dimensions: List[Dimension]

class RubricResponse(BaseModel):
    id: int
    name: str
    dimensions: List[Dict[str, Any]]

    class Config:
        orm_mode = True

class DimensionScoreResponse(BaseModel):
    dimension_name: str
    score: int
    data:str
    
class UserDataResponse(BaseModel):
    id: int
    name: str
    degree: str
    topic: str
    total_score: float
    scores: List[DimensionScoreResponse]