from backend.src.utils import process_pdf, process_docx, process_initial_agents
from backend.Agents.text_agents import summarize_and_analyze_agent, extract_scope_agent, scoped_suggestions_agent
from backend.src.types import QueryRequestThesisAndRubric, QueryRequestThesis,PostData,FeedbackData ,User, UserScore, Feedback, QueryScope
from backend.src.logic import CancellationToken, process_request
from backend.src.kafka_utils import increment_users, decrement_users, get_active_users, send_to_kafka, consume_messages, create_kafka_topic

from aiokafka import AIOKafkaProducer
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException ,Depends,  WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware 
import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
import uvicorn
import uuid

load_dotenv()

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


@app.get("/api/")
def read_root():
    return {"message": "Hello! This is the Dissertation Analysis! Dissertation Analysis app is running!"}


@app.websocket("/api/ws/notifications")
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


@app.websocket("/api/ws/dissertation_analysis_reconnect")
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


@app.post("/api/postUserData")
def post_user_data(postData: PostData, db: Session = Depends(get_db)):
    # Check if user exists based on unique combination of name, degree, and topic
    db_user = db.query(User).filter_by(
        name=postData.userData.name,
        degree=postData.userData.degree,
        topic=postData.userData.topic
    ).first()

    if db_user:
        # Update user total score
        db_user.total_score = postData.userData.total_score
    else:
        # Insert new user data if not exists
        db_user = User(
            name=postData.userData.name,
            degree=postData.userData.degree,
            topic=postData.userData.topic,
            total_score=postData.userData.total_score
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
            # Insert new score
            db_score = UserScore(
                user_id=db_user.id,
                dimension_name=score_data.dimension_name,
                score=score_data.score
            )
            db.add(db_score)
    
    db.commit()

    return {"message": "Data successfully stored", "user_id": db_user.id}


@app.post("/api/submitFeedback")
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


@app.post("/api/extract_text_from_file_and_analyze_images")
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


@app.post("/api/pre_analyze")
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


@app.post("/api/scope_extraction")
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


@app.post("/api/generate_scoped_feedback")
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


@app.websocket("/api/ws/dissertation_analysis")
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


def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)

if __name__ == "__main__":
    main()
