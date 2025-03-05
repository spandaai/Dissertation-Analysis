from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import Dict, Optional ,List
from typing_extensions import TypedDict

Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    degree = Column(String(255))
    topic = Column(Text)  
    total_score = Column(Integer)

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

class UserData(BaseModel):
    name: str
    degree: str
    topic: str
    total_score: float

class UserScoreData(BaseModel):
    dimension_name: str
    score: float

class PostData(BaseModel):
    userData: UserData
    userScores: List[UserScoreData]

class FeedbackData(BaseModel):
    selectedText: str
    feedback: str
    preAnalysisData: str

