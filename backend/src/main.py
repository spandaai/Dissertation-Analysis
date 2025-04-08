from backend.Agents.text_agents import summarize_and_analyze_agent, extract_scope_agent, scoped_suggestions_agent, scoring_agent
from backend.InferenceEngine.inference_engines import invoke_llm, ModelType
from backend.src.kafka_utils import increment_users, decrement_users, get_active_users, send_to_kafka, consume_messages, create_kafka_topic
from backend.src.logic import CancellationToken, process_request
from backend.src.types import User, UserScore, Feedback
from backend.src.types import *
from backend.src.utils import process_pdf, process_docx, process_initial_agents
import base64
from fastapi import FastAPI, Request, Response, params
from fastapi.responses import HTMLResponse, RedirectResponse
import json
from aiokafka import AIOKafkaProducer
import asyncio
from contextlib import asynccontextmanager
from backend.src.saml_utils import *
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException ,Depends,  WebSocketDisconnect,status
from fastapi.middleware.cors import CORSMiddleware 
import logging
from multiprocessing import Pool
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from time import time
import uvicorn
import uuid
import httpx
from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import Session, relationship
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from urllib.parse import unquote
import re
import redis 
import xml.etree.ElementTree as ET
load_dotenv()
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

#Get the database URL from environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "dissertation_analysis_queue")
MAX_CONCURRENT_USERS = int(os.getenv("MAX_CONCURRENT_USERS", 3))
producer = None
queue_lock = asyncio.Lock()
consumer_initialized = False
consumer_lock = asyncio.Lock()
consumer = None  # Single consumer instance
notification_clients = {}  # Map of session IDs to WebSocket connections
connected_websockets = {}
producer = None  # Single producer instance
consumer_task = None  # Single consumer task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  

# Configuration
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

# Database Engine
try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    print("Database connection established successfully.")
except OperationalError as e:
    print(f"Database connection failed: {e}")
    engine = None

# Session and Base
if engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
else:
    SessionLocal = None
    Base = None

# Initialize Database
def init_db():
    """Initialize the database tables."""
    if Base and engine:
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully.")
        except Exception as e:
            print(f"An error occurred during database initialization: {e}")
    else:
        print("Database engine is not initialized. Skipping table creation.")

# Dependency Injection for FastAPI
def get_db():
    """Provide a database session as a dependency."""
    if not SessionLocal:
        raise RuntimeError("Database session factory is not initialized.")
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"An error occurred during database session: {e}")
        raise
    finally:
        db.close()

# Initialize at startup
init_db()

@asynccontextmanager
async def lifespan(app):
    global producer

    try:
        # Initialize Kafka Producer
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            max_request_size=200000000  # Large message size
        )
        await producer.start()

        # Ensure Kafka topic exists
        await create_kafka_topic()

        # Start Kafka consumer
        consumer_task = asyncio.create_task(consume_messages())
        yield  # Run the app

    except Exception as e:
        print(f"Error during lifespan setup: {e}")

    finally:
        # Stop the Kafka producer and consumer
        if producer:
            await producer.stop()
        if consumer_task:
            consumer_task.cancel()
            await consumer_task


app = FastAPI(
    title="Dissertation Analysis API",
    description="API for analyzing dissertations",
    version="1.0.0",
    app = FastAPI(lifespan=lifespan)
)


# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, but you can specify a list of domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/dissertation/api/")
def read_root():
    return {"message": "Hello! This is the Dissertation Analysis! Dissertation Analysis app is running!"}


@app.websocket("/dissertation/api/ws/notifications")
async def notification_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for notifications.
    """
    try:
        await websocket.accept()

        # Receive the session ID from the frontend
        session_id = await websocket.receive_text()
        notification_clients[session_id] = websocket
        logger.info(f"Notification WebSocket established for session {session_id}")

        # Keep the WebSocket alive
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        logger.info(f"Notification WebSocket disconnected for session {session_id}")
        notification_clients.pop(session_id, None)


@app.websocket("/dissertation/api/ws/dissertation_analysis_reconnect")
async def websocket_reconnect(websocket: WebSocket, session_id: str):
    """
    Handle WebSocket reconnections for dequeued Kafka requests.
    """
    try:
        await websocket.accept()
        connected_websockets[session_id] = websocket
        logger.info(f"Frontend reconnected for session {session_id}")

        # Keep the WebSocket connection alive until processing completes
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        connected_websockets.pop(session_id, None)


@app.post("/dissertation/api/postUserData")
def post_user_data(postData: PostData, request: Request, db: Session = Depends(get_db)):
    # Get session_id from cookies
    session_id = request.cookies.get("session_id")
    
    # Default evaluator value in case session retrieval fails
    evaluator = "unknown"
    
    # Get evaluator name from session if session_id exists
    if session_id:
        try:
            # Get user data from Redis
            user_data_str = redis_client.get(session_id)
            if user_data_str:
                user_data = json.loads(user_data_str)
                evaluator = user_data.get("name", "unknown")
        except Exception as e:
            # Log the error but continue with default evaluator
            print(f"Error retrieving session data: {e}")
    
    # Check if user exists based on unique combination of name, degree, and topic
    db_user = db.query(User).filter_by(
        name=postData.userData.name,
        degree=postData.userData.degree,
        topic=postData.userData.topic,
        evaluator=evaluator  # Use the evaluator from session
    ).first()
    print("evaluator",evaluator)
    if db_user:
        # Update user total score
        db_user.total_score = postData.userData.total_score
    else:
        # Insert new user data if not exists
        db_user = User(
            name=postData.userData.name,
            degree=postData.userData.degree,
            topic=postData.userData.topic,
            total_score=postData.userData.total_score,
            evaluator=evaluator  # Use the evaluator from session
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    # Update or insert user score data
    existing_scores = {score.dimension_name: score for score in db_user.scores}
    for score_data in postData.userScores:
        if score_data.dimension_name in existing_scores:
            # Update existing score
            existing_scores[score_data.dimension_name].score = score_data.score
        else:
            print("postData.userScores",score_data.data)
            # Insert new score
            db_score = UserScore(
                user_id=db_user.id,
                dimension_name=score_data.dimension_name,
                score=score_data.score,
                data=score_data.data
            )
            db.add(db_score)
    
    db.commit()

    return {"message": "Data successfully stored", "user_id": db_user.id}


@app.post("/dissertation/api/submitFeedback")
def submit_feedback(feedback_data: FeedbackData, db: Session = Depends(get_db)):
    try:
        # Insert the feedback into the database
        feedback_entry = Feedback(
            selected_text=feedback_data.selectedText,
            feedback=feedback_data.feedback,
            pre_analysis=feedback_data.preAnalysisData
        )
        db.add(feedback_entry)
        db.commit()
        db.refresh(feedback_entry)

        return {"message": "Feedback stored successfully", "feedback_id": feedback_entry.id}
    
    except Exception as e:
        db.rollback()  # Ensure rollback on error
        print(f"Error inserting feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/dissertation/api/extract_text_from_file_and_analyze_images")
async def analyze_file(file: UploadFile = File(...)):
    try:
        if file.filename.endswith(".pdf"):
            return await process_pdf(file)
        elif file.filename.endswith(".docx"):
            return await process_docx(file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")
    except Exception as e:
        logger.exception("An error occurred while processing the file.")
        raise HTTPException(status_code=500, detail="Failed to process the file. Please try again.") from e


@app.post("/dissertation/api/pre_analyze")
async def pre_analysis(request: QueryRequestThesis):
    try:
        # Process initial agents in batch
        initial_results = await process_initial_agents(request.thesis)
        
        # Use the topic from batch results for summary
        summary_of_thesis = await summarize_and_analyze_agent(
            request.thesis, 
            initial_results["topic"]
        )
        
        response = {
            "degree": initial_results["degree"],
            "name": initial_results["name"],
            "topic": initial_results["topic"],
            "pre_analyzed_summary": summary_of_thesis
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to pre-analyze thesis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to pre-analyze thesis"
        )


@app.post("/dissertation/api/scope_extraction")
async def scope_extractor(dissertation_pre_analysis: QueryRequestThesis):
    try:
        # Extract scope of agent from pre analysis
        scope = await extract_scope_agent(dissertation_pre_analysis.thesis)
        
        return scope
        
    except Exception as e:
        logger.error(f"Failed to extract scope of thesis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to extract scope of thesis"
        )


@app.post("/dissertation/api/generate_scoped_feedback")
async def scoped_feedback(request: QueryScope):
    try:
        # Extract scope of agent from pre analysis
        scoped_feedback = await scoped_suggestions_agent(request.feedback, request.scope)
        
        return scoped_feedback
        
    except Exception as e:
        logger.error(f"Failed to extract scoped feedback of thesis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to extract scoped feedback of thesis"
        )


@app.websocket("/dissertation/api/ws/dissertation_analysis")
async def websocket_dissertation(websocket: WebSocket):
    """
    WebSocket endpoint for dissertation analysis.
    Handles direct WebSocket calls.
    """
    cancellation_token = CancellationToken()

    try:
        # Accept WebSocket connection
        await websocket.accept()

        # Receive initial data
        data = await websocket.receive_json()

        # Parse the request
        try:
            request = QueryRequestThesisAndRubric(**data)
        except Exception as e:
            logger.error(f"Payload parsing error: {e}")
            await websocket.send_json({"type": "error", "data": {"message": "Invalid payload structure"}})
            return


        # Check for specific metadata placeholders
        metadata_issues = []
        if request.pre_analysis.degree == "no_degree_found":
            metadata_issues.append("degree")
        if request.pre_analysis.name == "no_name_found":
            metadata_issues.append("name")
        if request.pre_analysis.topic == "no_topic_found":
            metadata_issues.append("topic")

        # If any metadata is problematic, send an error
        if metadata_issues:
            await websocket.send_json({
                "type": "error", 
                "data": {
                    "message": f"Due to an unexpected input format of the file, the system was unable to extract {', '.join(metadata_issues)} information. Please report this issue to the development team with details about the dissertation file. Provide the file and context to help us improve our analysis capabilities."
                }
            })
            await websocket.close()
            return
        
        # Extract details
        degree_of_student = request.pre_analysis.degree
        name_of_author = request.pre_analysis.name
        topic = request.pre_analysis.topic
        logger.info(f"Processing request for {name_of_author} on topic {topic}")

        # Check slot availability
        active_users = await get_active_users()
        if active_users >= MAX_CONCURRENT_USERS:
            logger.info(f"No slots available. Queuing request for {name_of_author}")

            try:
                # Generate session ID for tracking
                session_id = str(uuid.uuid4())
                data["session_id"] = session_id

                # Send the request to Kafka
                await send_to_kafka(data)

                # Notify the frontend
                await websocket.send_json({
                    "type": "queue_status",
                    "data": {"message": "Your request has been queued. Please wait...", "session_id": session_id}
                })
            except Exception as e:
                logger.error(f"Error queuing request: {e}")
            finally:
                # Close the WebSocket connection after queuing
                await websocket.close()
            return

        # Increment active users for direct requests
        await increment_users()

        # Process the request immediately
        await process_request(websocket, request, cancellation_token)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected during processing.")
    except Exception as e:
        logger.error(f"Error in WebSocket processing: {e}")
        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
    finally:
        # Decrement users only if it was a direct request
        if not cancellation_token.ws_closed:
            await websocket.close()
        await decrement_users()



    # Database Models

@app.post("/dissertation/api/dissertation_analysis")
async def post_dissertation(request: QueryRequestThesisAndRubric, db: Session = Depends(get_db)):
    """
    Post endpoint for dissertation analysis.
    Handles direct single dissertation call.
    """
    ###### please fix this ty <3
    evaluator = "unknown"
    result = dict()
    try:
        logger.info(f"Processing request for {request.pre_analysis.name} on topic {request.pre_analysis.topic}")
        # Process the request immediately
        result = await process_request(request)
    except Exception as e:
        logger.error(f"Error in processing: {e}")
        return {"type": "error", "data": {"message": str(e)}}
    
    if result:
        try:
            if isinstance(db, params.Depends):
                db = SessionLocal()
            db_user = User(
                    name=result['name'],
                    degree=result['degree'],
                    topic=result['topic'],
                    total_score=result['total_score'],
                    evaluator=evaluator  # Use the evaluator from session
                )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        
        except IntegrityError as e:
            db.rollback()  # Ensure rollback on error
            print('entry already exists, skipping')
            
        db_user = db.query(User).filter_by(
            name=result['name'],
            degree=result['degree'],
            topic=result['topic'],
        ).first()
        
        try:
            if db_user is not None:
                for criterion in result["criteria_evaluations"]:
                    score_entry = UserScore(
                        user_id = db_user.id,
                        dimension_name = criterion,
                        score = result["criteria_evaluations"][criterion]['score'],
                        data = result["criteria_evaluations"][criterion]['feedback']
                    )
                    db.add(score_entry)
                    db.commit()
                    db.refresh(score_entry)
        except Exception as e:
            db.rollback()  # Ensure rollback on error
            print(f"Error inserting user data: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    
    return result

@app.post("/dissertation/api/batch_input")
async def batch_upload(files: List[UploadFile] = File(...), process_count: int|None = None, db: Session = Depends(get_db)):
    ### counting on vllm's capablity to handle multiple simultaneous requests and switch out gpu ram
    # with Pool(processes = process_count) as pool:
    #     pool.map(spawner, files)
    for file in files:
        await spawner(file)


async def spawner(file: UploadFile):
    try:
        thesis_obj = await analyze_file(file)
        thesis_request = QueryRequestThesis(
            thesis = thesis_obj['text_and_image_analysis']
        )
        summary_request = QueryRequestThesisAndRubric(
            # rubric = dict(),    #### fill this please
            rubric={
            "criterion1": {
                "criteria_explanation": "Explanation for criterion1",
                "criteria_output": "Output for criterion1",
                "score_explanation": "Explanation for scoring criterion1"
            },
            "criterion2": {
                "criteria_explanation": "Explanation for criterion2",
                "criteria_output": "Output for criterion2",
                "score_explanation": "Explanation for scoring criterion2"
            }
        },
            pre_analysis = await pre_analysis(thesis_request)
            #### not adding feedback rn
        )
        result = await post_dissertation(summary_request)   ## this will handle db parts too
        return
    except Exception as e:
        print('exception in spawner')
        print(e)

@app.get("/dissertation/api/dbtest")
async def test_sql(db: Session = Depends(get_db)):
    print(type(db))
    print(isinstance(db, params.Depends))
    ## SAMPLE adding an entry
    # db_user = User(
    #         name='test1',
    #         degree='test1',
    #         topic='test1',
    #         total_score=1,
    #         evaluator='test1'  # Use the evaluator from session
    #     )
    # db.add(db_user)
    # db.commit()
    # db.refresh(db_user)

    ## SAMPLE querying an entry
    res = db.query(User).all()
    for user in res:
        print(user.name)
    return

async def verify_session_middleware(request: Request, allowed_roles: list = None):
    session_id = request.cookies.get("session_id")
    user_role_cookie = request.cookies.get("user_role")

    if not session_id or not user_role_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    user_data_json = redis_client.get(session_id)
    if not user_data_json:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )

    try:
        user_data = json.loads(user_data_json)

        if user_data.get("role") != user_role_cookie:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )

        if allowed_roles and user_data.get("role").lower() not in [role.lower() for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )

        request.state.user_data = user_data
        return user_data  # This return was missing
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


def get_verified_user(allowed_roles: list = None):
    """Returns a dependency function that verifies session with allowed roles"""
    async def dependency(request: Request):
        user_data = await verify_session_middleware(request, allowed_roles)
        return user_data

    return dependency

@app.get("/dissertation/api/rubrics", response_model=List[RubricResponse])
async def get_all_rubrics(
    request: Request,  # Missing request parameter
    user_data: dict = Depends(get_verified_user(["staff", "STAFF", "admin", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Get all rubrics"""
    print("USER DATA",user_data)
    try:
        rubrics = db.query(Rubric).all()
        return rubrics
    except Exception as e:
        logger.error(f"Error fetching rubrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching rubrics"
        )

@app.get("/dissertation/api/users", response_model=List[UserDataResponse])
async def get_users_by_name(
    request: Request,
    user_data: dict = Depends(get_verified_user(["staff", "STAFF", "admin", "ADMIN"])),
    db: Session = Depends(get_db)
):
    name = user_data.get("name")

    if not name:
        raise HTTPException(status_code=400, detail="Name not found in session")

    users = db.query(User).filter(User.evaluator == name).all()

    if not users:
        raise HTTPException(status_code=404, detail=f"No users found with name {name}")

    return [
        UserDataResponse(
            id=user.id,
            name=user.name,
            degree=user.degree,
            topic=user.topic,
            total_score=user.total_score,
            scores=[
                DimensionScoreResponse(
                    dimension_name=score.dimension_name,
                    score=score.score,
                    data=score.data
                ) for score in user.scores
            ]
        ) for user in users
    ]


@app.put("/dissertation/api/users/{user_id}/scores")
async def update_user_scores(
    user_id: int, 
    scores: List[DimensionScoreResponse],
    request: Request,  
    user_data: dict = Depends(get_verified_user(["staff", "STAFF", "admin", "ADMIN"])),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    
    # Update user scores
    for score_update in scores:
        score_obj = db.query(UserScore).filter(
            UserScore.user_id == user_id,
            UserScore.dimension_name == score_update.dimension_name
        ).first()
        
        if score_obj:
            score_obj.score = score_update.score
    
    # Recalculate total score
    total_score = sum(score.score for score in user.scores)
    user.total_score = total_score
    
    db.commit()
    
    return {
        "message": "Scores updated successfully",
        "user_id": user_id,
        "total_score": total_score
    }

@app.get("/dissertation/api/rubrics/{rubric_id}", response_model=RubricResponse)
async def get_rubric_by_id(rubric_id: int, 
    request: Request,  # Missing request parameter
    user_data: dict = Depends(get_verified_user(["staff", "STAFF", "admin", "ADMIN"])),
    db: Session = Depends(get_db)):
    """Get a specific rubric by ID"""
    try:
        rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
        if not rubric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rubric with ID {rubric_id} not found"
            )
        return rubric
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching rubric {rubric_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching rubric"
        )

@app.post("/dissertation/api/rubrics", response_model=RubricResponse, status_code=status.HTTP_201_CREATED)
async def create_rubric(rubric: RubricCreate,
    request: Request,  # Missing request parameter
    user_data: dict = Depends(get_verified_user(["staff", "STAFF", "admin", "ADMIN"])),
      db: Session = Depends(get_db)):
    """Create a new rubric"""
    try:
        # Check for existing rubric with same name
        existing_rubric = db.query(Rubric).filter(Rubric.name == rubric.name).first()
        if existing_rubric:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rubric with name '{rubric.name}' already exists"
            )
        
        # Create new rubric
        db_rubric = Rubric(
            name=rubric.name,
            dimensions=[dimension.dict() for dimension in rubric.dimensions]
        )
        db.add(db_rubric)
        db.commit()
        db.refresh(db_rubric)
        return db_rubric
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating rubric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating rubric"
        )

@app.put("/dissertation/api/rubrics/{rubric_id}", response_model=RubricResponse)
async def update_rubric(rubric_id: int, rubric: RubricUpdate,
    request: Request,  # Missing request parameter
    user_data: dict = Depends(get_verified_user(["staff", "STAFF", "admin", "ADMIN"])),db: Session = Depends(get_db)):
    """Update an existing rubric"""
    try:
        # Get existing rubric
        db_rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
        if not db_rubric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rubric with ID {rubric_id} not found"
            )
        
        # Check for name conflict (if name is changing)
        if rubric.name != db_rubric.name:
            name_conflict = db.query(Rubric).filter(
                Rubric.name == rubric.name,
                Rubric.id != rubric_id
            ).first()
            if name_conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rubric with name '{rubric.name}' already exists"
                )
        
        # Update rubric
        db_rubric.name = rubric.name
        db_rubric.dimensions = [dimension.dict() for dimension in rubric.dimensions]
        
        db.commit()
        db.refresh(db_rubric)
        return db_rubric
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating rubric {rubric_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating rubric"
        )

@app.delete("/dissertation/api/rubrics/{rubric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rubric(rubric_id: int,
    request: Request,  # Missing request parameter
    user_data: dict = Depends(get_verified_user(["staff", "STAFF", "admin", "ADMIN"])), db: Session = Depends(get_db)):
    """Delete a rubric"""
    try:
        # Get existing rubric
        db_rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
        if not db_rubric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rubric with ID {rubric_id} not found"
            )
        
        # Delete rubric
        db.delete(db_rubric)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting rubric {rubric_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting rubric"
        )




@app.get("/dissertation/api/login")
def login():
    authn_request = create_authn_request()
    encoded_request = compress_and_encode_request(authn_request)
    return Response(content=encoded_request, media_type="text/plain")


@app.get('/dissertation/api/logout')
async def handle_logout(request: Request, response: Response):
    # Get session_id from cookies
    session_id = request.cookies.get("session_id")
    user_role = request.cookies.get("user_role")
    
    if session_id:
        redis_client.delete(session_id)

    if user_role:
        redis_client.delete(user_role)
    
    # Clear session_id cookie
    response.set_cookie(key="session_id", value="", httponly=True, secure=True, max_age=0, samesite="None")
    response.set_cookie(key="user_role", value="", httponly=True, secure=True, max_age=0, samesite="None")
    
    # Return success response with redirect URL
    return {"success": True, "redirect_url": "https://elearn.bits-pilani.ac.in/user/"}



redis_client = redis.StrictRedis(host="localhost", port=6379, decode_responses=True)

# In-memory storage
stored_data = {
    "api_data": None
}

@app.post("/dissertation/Shibboleth.sso/SAML2/POST")
async def receive_saml_response(request: Request):
    form_data = await request.form()
    saml_response = form_data.get("SAMLResponse")

    if not saml_response:
        return HTMLResponse(content="<h1>SAMLResponse parameter missing</h1>", status_code=400)

    try:
        # Decode the SAMLResponse
        decoded_response = base64.b64decode(saml_response).decode("utf-8")
        
        # Parse the XML to extract the NameID and other attributes
        root = ET.fromstring(decoded_response)
        namespace = {
            "saml2": "urn:oasis:names:tc:SAML:2.0:assertion",
            "saml2p": "urn:oasis:names:tc:SAML:2.0:protocol"
        }
        
        # Extract NameID
        name_id_element = root.find(".//saml2:NameID", namespace)
        if name_id_element is None:
            return HTMLResponse(content="<h1>NameID not found in SAMLResponse</h1>", status_code=400)
        name_id = name_id_element.text
        
        # Extract user's name (cn attribute)
        cn_element = root.find(".//saml2:Attribute[@FriendlyName='cn']/saml2:AttributeValue", namespace)
        user_name = cn_element.text if cn_element is not None else "Unknown User"
        
        # Extract user's role (employeeType attribute)
        role_element = root.find(".//saml2:Attribute[@FriendlyName='employeeType']/saml2:AttributeValue", namespace)
        user_role = role_element.text if role_element is not None else "unknown"
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Store user data in Redis as JSON string
        user_data = {
            "email": name_id,
            "name": user_name,
            "role": user_role
        }
        redis_client.setex(session_id, 3600, json.dumps(user_data))

        redirect_url = "http://localhost:4002/HomePage"
        response = HTMLResponse(content=f"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="0; url={redirect_url}">
                </head>
                <body>
                    <p>Redirecting...</p>
                </body>
            </html>
        """, status_code=200)
        
        # Set the session ID in the cookie
        response.set_cookie(key="session_id", value=session_id, httponly=True, secure=True, max_age=3600, samesite="None")
        response.set_cookie(key="user_role", value=user_role, httponly=False, secure=True, max_age=3600, samesite="None")

        return response

    except Exception as e:
        return HTMLResponse(content=f"<h1>Error processing SAMLResponse: {str(e)}</h1>", status_code=500)
    

    
@app.get("/dissertation/Shibboleth.sso/SLO/Redirect")
async def handle_slo_redirect(request: Request):
    """
    Handle SAML Logout Response via Redirect binding.
    """
    try:
        saml_response = request.query_params.get("SAMLResponse")
        if not saml_response:
            logging.error("SAMLResponse parameter is missing")
            raise HTTPException(status_code=400, detail="SAMLResponse parameter is missing")

        url_decoded_response = unquote(saml_response)
        logging.info("URL-decoded SAMLResponse: %s", url_decoded_response)

        decoded_response = base64.b64decode(url_decoded_response).decode("utf-8")
        logging.info("Decoded SAMLResponse: %s", decoded_response)

        return {
            "message": "SAML Logout Response processed successfully",
            "decoded_response": decoded_response,
        }

    except base64.binascii.Error as e:
        logging.error("Error decoding Base64 SAMLResponse: %s", str(e))
        raise HTTPException(status_code=400, detail="Invalid Base64 encoding in SAMLResponse")
    except Exception as e:
        logging.error("Unexpected error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to process SAML Logout Response")

@app.post("/dissertation/api/verify-session")
async def verify_session(request: Request):
    # Get session ID and user role from cookies
    session_id = request.cookies.get("session_id")
    user_role_cookie = request.cookies.get("user_role")

    if not session_id or not user_role_cookie:
        return {"isValid": False}

    # Check if the session exists in Redis
    user_data_json = redis_client.get(session_id)
    if not user_data_json:
        return {"isValid": False}
        
    # Parse the user data from Redis
    try:
        user_data = json.loads(user_data_json)
        # Check if the user role in Redis matches the cookie
        if user_data.get("role") == user_role_cookie:
            return {"isValid": True}
        else:
            return {"isValid": False}
    except Exception as e:
        print(f"Error verifying session: {e}")
        return {"isValid": False}



@app.get("/dissertation/api/get-saml-data")
async def get_saml_data():
    """
    Endpoint to fetch stored decoded response and API data.
    """
    return JSONResponse(content=stored_data)

def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)

if __name__ == "__main__":
    main()
