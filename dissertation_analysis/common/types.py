# This module defines database models, data validation schemas, and supporting classes for a thesis evaluation system.

# Database Models:
# - `User`: Represents a user in the system with attributes for name, degree, topic, and total score. 
#           It includes a relationship to the `UserScore` model and enforces a unique constraint on (name, degree, topic).
# - `UserScore`: Stores individual dimension scores for users, related to the `User` model by foreign key.
# - `Feedback`: Stores feedback data for thesis analysis, including selected text, feedback, and pre-analysis information.

# Helper Classes:
# - `CancellationToken`: Provides cancellation and WebSocket closure control for async operations.
#   - `cancel()`: Sets cancellation flag.
#   - `mark_closed()`: Marks the WebSocket as closed.

# Typed Dictionary:
# - `RubricCriteria`: Defines a structure for rubric criteria, score explanations, and criteria outputs.

# Pydantic Models:
# - `PreAnalysis`: Models pre-analyzed thesis summary data for validation and parsing.
# - `QueryRequestThesisAndRubric`: Handles incoming requests containing thesis rubric and pre-analysis data.
# - `QueryRequestThesis`: Handles requests containing thesis text only.
# - `UserData`: Represents user information for API requests or responses.
# - `UserScoreData`: Captures individual score data for specific thesis evaluation dimensions.
# - `PostData`: Encapsulates user and score data for bulk posting operations.
# - `FeedbackData`: Captures feedback information including selected text and pre-analysis data.


from typing import Dict, Optional ,List, Tuple
from pydantic import BaseModel
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Base64Response(BaseModel):
    base64_string: str = Field(..., description="Base64 encoded string of the image")

class ResizeImageRequest(BaseModel):
    max_size: Optional[int] = Field(default=800, description="Maximum allowed size for any dimension")
    min_size: Optional[int] = Field(default=70, description="Minimum allowed size for any dimension")

class TextCleaningRequest(BaseModel):
    text: str = Field(..., description="Text to be cleaned")

class TextResponse(BaseModel):
    text: str = Field(..., description="Cleaned text")

# Add these models to your type definitions
class TextChunkRequest(BaseModel):
    text: str = Field(..., description="The text to be chunked")
    chunk_size: Optional[int] = Field(default=1000, description="Target size for each chunk in words")

class FirstNWordsRequest(BaseModel):
    text: str = Field(..., description="The input text")
    n: int = Field(..., description="Number of words to extract", gt=0)

class ChunkResponse(BaseModel):
    chunks: List[Tuple[str, int]] = Field(..., description="List of tuples containing (chunk_text, word_count)")

class FirstNWordsResponse(BaseModel):
    text: str = Field(..., description="Extracted text containing first N words")
    word_count: int = Field(..., description="Actual number of words returned")


# Add this new model class with your other type definitions
class BatchImageProcessingRequest(BaseModel):
    images_data: List[Tuple[int, bytes]]
    batch_size: int = 5

# Request Model for Scoring Agent
class ScoringRequest(BaseModel):
    analysis: str
    criteria: str
    score_guidelines: str
    criteria_guidelines: str
    feedback: str

class ChunkSummarizationProcessingRequest(BaseModel):
    chunks: List[str]
    system_prompt: str
    batch_size: int = 5

class DocumentText(BaseModel):
    document_text: str

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


class CancellationToken:
    def __init__(self):
        self.is_cancelled = False
        self.ws_closed = False

    def cancel(self):
        self.is_cancelled = True

    def mark_closed(self):
        self.ws_closed = True


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

