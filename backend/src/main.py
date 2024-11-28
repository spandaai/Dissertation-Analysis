from backend.src.utils import *
from backend.src.image_agents import *
import uvicorn
from backend.src.agents import *
from backend.src.dissertation_types import QueryRequestThesisAndRubric, QueryRequestThesis,UserData,UserScoreData,PostData,FeedbackData ,User, UserScore, Feedback
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException ,Depends,  WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware 
import re
import fitz
import logging
from io import BytesIO
from docx import Document
from docx.parts.image import ImagePart
from PIL import Image
from typing import Dict, Tuple
import asyncio
from collections import OrderedDict, deque
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer, TopicPartition, OffsetAndMetadata
from kafka.admin import KafkaAdminClient, NewTopic
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
import json
import base64
from sqlalchemy.exc import OperationalError
import uuid

load_dotenv()

#Get the database URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    print("Database connection established successfully.")
except OperationalError as e:
    # Handle SQLAlchemy operational errors
    print(f"Database connection failed: {e}")
    engine = None
    SessionLocal = None
    Base = None
except Exception as e:
    # Handle other unexpected errors
    print(f"An unexpected error occurred: {e}")
    engine = None
    SessionLocal = None
    Base = None

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "dissertation_analysis_queue")
current_users = 0
MAX_CONCURRENT_USERS = int(os.getenv("MAX_CONCURRENT_USERS", 3))

producer = None
queue_lock = asyncio.Lock()
user_lock = asyncio.Lock()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  

async def create_kafka_topic():
    """Ensure the Kafka topic exists."""
    admin_client = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        client_id="dissertation_analysis_admin"
    )
    topic_list = admin_client.list_topics()
    if KAFKA_TOPIC not in topic_list:
        try:
            admin_client.create_topics([NewTopic(
                name=KAFKA_TOPIC,
                num_partitions=1,
                replication_factor=1
            )])
            logger.info(f"Kafka topic '{KAFKA_TOPIC}' created successfully.")
        except Exception as e:
            logger.error(f"Error creating Kafka topic: {e}")
    else:
        logger.info(f"Kafka topic '{KAFKA_TOPIC}' already exists.")
    admin_client.close()



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


def init_db():
    """Initialize the database."""
    try:
        if engine is not None:  # Ensure the engine is initialized
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully.")
        else:
            print("Database engine is not initialized. Skipping table creation.")
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")


def get_db():
    """Provide a database session."""
    if SessionLocal is None:
        print("SessionLocal is not initialized. Database session cannot be provided.")
        return  # Optionally raise an exception if critical
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"An error occurred during database session: {e}")
    finally:
        db.close()

init_db()
# Create FastAPI app instance


origins = [
    "http://localhost",
    "http://localhost:4000",

]
# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, but you can specify a list of domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def read_root():
    return {"message": "Hello! This is the Dissertation Analysis! Dissertation Analysis app is running!"}

async def increment_users():
    global current_users
    async with user_lock:
        current_users += 1
        logger.info(f"Incremented users: {current_users}")
        return current_users

async def decrement_users():
    global current_users
    async with user_lock:
        current_users = max(0, current_users - 1)
        logger.info(f"Decremented users: {current_users}")
        return current_users

async def get_active_users():
    global current_users
    async with user_lock:
        return current_users

consumer_initialized = False




producer = None  # Single producer instance
consumer_task = None  # Single consumer task

async def send_to_kafka(message: dict):
    """
    Send a message to the Kafka queue and start the consumer if needed.
    """
    global producer, consumer_task
    if not producer:
        try:
            logger.info("Initializing Kafka producer...")
            producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                max_request_size=200000000
            )
            await producer.start()
            logger.info("Kafka producer initialized.")
        except Exception as e:
            logger.error(f"Error initializing Kafka producer: {e}")
            return

    try:
        # Check payload size
        payload = json.dumps(message).encode("utf-8")
        logger.info(f"Payload size: {len(payload)} bytes")
        
        # Send message
        logger.info(f"Sending message to Kafka: {message}")
        await producer.send_and_wait(KAFKA_TOPIC, payload)
        logger.info("Message successfully sent to Kafka.")

        # Start consumer if not already running
        if not consumer_task or consumer_task.done():
            logger.info("Starting Kafka consumer task...")
            consumer_task = asyncio.create_task(consume_messages())
    except Exception as e:
        logger.error(f"Error sending message to Kafka: {e}")
        if "UNKNOWN_TOPIC_OR_PARTITION" in str(e):
            logger.info("Topic not found. Creating topic...")
            try:
                await create_kafka_topic()
                await producer.send_and_wait(KAFKA_TOPIC, payload)
                logger.info(f"Message sent successfully after creating topic '{KAFKA_TOPIC}'.")
            except Exception as topic_creation_error:
                logger.error(f"Error creating topic or resending message: {topic_creation_error}")



consumer_lock = asyncio.Lock()
consumer = None  # Single consumer instance


async def process_dequeued_request(data: dict, session_id: str):
    """
    Process a dequeued Kafka request using a reconnected WebSocket.
    """
    try:
        # Notify the frontend to reconnect
        await notify_frontend_to_reconnect(session_id)

        # Wait for the frontend to reconnect
        websocket = await wait_for_websocket_reconnect(session_id)

        # Process the request via the reconnected WebSocket
        request = QueryRequestThesisAndRubric(**data)
        await process_request(websocket, request, CancellationToken())

    except Exception as e:
        logger.error(f"Error processing dequeued request for session {session_id}: {e}")
    finally:
        # Decrement active users after processing
        await decrement_users()



async def consume_messages():
    """
    Consume messages from Kafka and process them using a real WebSocket connection.
    """
    global consumer
    if consumer is None:
        consumer = AIOKafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="dissertation_analysis_consumer",
            auto_offset_reset="earliest",
        )
        await consumer.start()

    try:
        async for msg in consumer:
            # Wait for a slot to become available
            while await get_active_users() >= MAX_CONCURRENT_USERS:
                await asyncio.sleep(1)

            # Increment active users for dequeued requests
            await increment_users()

            try:
                # Parse Kafka message
                data = json.loads(msg.value.decode("utf-8"))
                session_id = data.get("session_id")
                if not session_id:
                    logger.error("Session ID missing in Kafka message. Skipping.")
                    await decrement_users()
                    continue

                # Commit the Kafka offset immediately
                await consumer.commit({
                    TopicPartition(KAFKA_TOPIC, msg.partition): OffsetAndMetadata(msg.offset + 1, "")
                })
                logger.info(f"Committed Kafka offset {msg.offset + 1} for session {session_id}.")

                # Process the request in a separate task
                asyncio.create_task(process_dequeued_request(data, session_id))

            except Exception as e:
                logger.error(f"Error processing Kafka message: {e}")
                await decrement_users()  # Ensure active users count is decremented in case of failure

    finally:
        await consumer.stop()


notification_clients = {}  # Map of session IDs to WebSocket connections

@app.websocket("/ws/notifications")
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


async def notify_frontend_to_reconnect(session_id: str):
    """
    Notify the frontend to reconnect for the given session ID.
    """
    try:
        websocket = notification_clients.get(session_id)
        if websocket:
            await websocket.send_json({"type": "reconnect", "session_id": session_id})
            logger.info(f"Notified frontend to reconnect for session {session_id}")
        else:
            logger.warning(f"No active notification WebSocket for session {session_id}")
    except Exception as e:
        logger.error(f"Error notifying frontend for session {session_id}: {e}")



connected_websockets = {}

@app.websocket("/ws/dissertation_analysis_reconnect")
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



async def wait_for_websocket_reconnect(session_id: str, timeout: int = 30):
    """
    Wait for the frontend to reconnect within the timeout period.
    """
    logger.info(f"Waiting for frontend to reconnect for session {session_id}")
    for _ in range(timeout):
        if session_id in connected_websockets:
            logger.info(f"Frontend reconnected for session {session_id}")
            return connected_websockets[session_id]
        await asyncio.sleep(1)
    raise TimeoutError(f"Frontend did not reconnect for session {session_id}")



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
    # Insert the feedback into the database
    feedback_entry = Feedback(
        selected_text=feedback_data.selectedText,
        feedback=feedback_data.feedback
    )
    db.add(feedback_entry)
    db.commit()
    db.refresh(feedback_entry)

    return {"message": "Feedback stored successfully", "feedback_id": feedback_entry.id}




@app.post("/extract_text_from_file_and_analyze_images")
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


class CancellationToken:
    def __init__(self):
        self.is_cancelled = False
        self.ws_closed = False

    def cancel(self):
        self.is_cancelled = True

    def mark_closed(self):
        self.ws_closed = True

async def safe_send(websocket: WebSocket, cancellation_token: CancellationToken, message: dict) -> bool:
    """Safely send a message through the WebSocket if it's still open"""
    if not cancellation_token.ws_closed:
        try:
            await websocket.send_json(message)
            return True
        except RuntimeError as e:
            print(f"WebSocket send failed: {str(e)}")
            cancellation_token.mark_closed()
            return False
    return False


async def process_request(websocket: WebSocket, request: QueryRequestThesisAndRubric, cancellation_token: CancellationToken):
    """
    Process the dissertation analysis request and stream results via the WebSocket.
    """
    try:
        # Send initial metadata to the frontend
        degree_of_student = request.pre_analysis.degree
        name_of_author = request.pre_analysis.name
        topic = request.pre_analysis.topic

        await websocket.send_json({
            "type": "metadata",
            "data": {
                "name": name_of_author,
                "degree": degree_of_student,
                "topic": topic
            }
        })

        # Dissertation evaluation process
        dissertation_system_prompt = """You are an impartial academic evaluator - an expert in analyzing the summarized dissertation provided to you. 
Your task is to assess the quality of the provided summarized dissertation in relation to specific evaluation criteria."""

        evaluation_results = {}
        total_score = 0

        # Process each rubric criterion
        for criterion, explanation in request.rubric.items():
            if cancellation_token.is_cancelled:
                logger.info(f"Processing canceled for criterion: {criterion}")
                break

            # Build the user prompt for this criterion
            dissertation_user_prompt = f"""
# Input Materials
## Dissertation Text
{request.pre_analysis.pre_analyzed_summary}

## Evaluation Context
- Author: {name_of_author}
- Academic Field: {degree_of_student}

## Assessment Criterion and its explanation
### {criterion}:
#### Explanation: {explanation['criteria_explanation']}

{explanation['criteria_output']}

Please make sure that you critique the work heavily, including all improvements that can be made.

DO NOT SCORE THE DISSERTATION, YOU ARE TO PROVIDE ONLY DETAILED ANALYSIS, AND NO SCORES ASSOCIATED WITH IT.
"""
            if request.feedback:
                dissertation_user_prompt += f'\nIMPORTANT(The following feedback was provided by an expert. Consider the feedback properly, and ensure your evaluation follows this feedback): {request.feedback}'

            # Notify the frontend about the start of the criterion evaluation
            await websocket.send_json({
                "type": "criterion_start",
                "data": {"criterion": criterion}
            })

            # Stream analysis results to the client
            analysis_chunks = []
            try:
                async for chunk in stream_llm(
                    system_prompt=dissertation_system_prompt,
                    user_prompt=dissertation_user_prompt,
                    model_type=ModelType.ANALYSIS,
                    cancellation_token=cancellation_token
                ):
                    if cancellation_token.is_cancelled:
                        logger.info(f"Streaming canceled for criterion: {criterion}")
                        break

                    analysis_chunks.append(chunk)
                    await websocket.send_json({
                        "type": "analysis_chunk",
                        "data": {
                            "criterion": criterion,
                            "chunk": chunk
                        }
                    })

                if not cancellation_token.is_cancelled:
                    analyzed_dissertation = "".join(analysis_chunks)

                    # Perform scoring
                    graded_response = await scoring_agent(
                        analyzed_dissertation, 
                        criterion, 
                        explanation['score_explanation'], 
                        explanation['criteria_explanation'],
                        request.feedback
                    )

                    # Extract score using regex
                    pattern = r"spanda_score\s*:\s*(?:\*{1,2}\s*)?(\d+(?:\.\d+)?)\s*(?:\*{1,2})?"
                    match = re.search(pattern, graded_response, re.IGNORECASE)
                    score = float(match.group(1)) if match else 0
                    total_score += score

                    # Send criterion completion details
                    await websocket.send_json({
                        "type": "criterion_complete",
                        "data": {
                            "criterion": criterion,
                            "score": score,
                            "full_analysis": analyzed_dissertation
                        }
                    })

                    evaluation_results[criterion] = {
                        "feedback": analyzed_dissertation,
                        "score": score
                    }

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected during analysis of criterion: {criterion}")
                cancellation_token.mark_closed()
                break
            except Exception as e:
                logger.error(f"Error processing criterion {criterion}: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "message": f"Error processing criterion {criterion}: {str(e)}",
                        "criterion": criterion
                    }
                })
                break

        # Send final evaluation results
        if not cancellation_token.is_cancelled:
            await websocket.send_json({
                "type": "complete",
                "data": {
                    "criteria_evaluations": evaluation_results,
                    "total_score": total_score,
                    "name": name_of_author,
                    "degree": degree_of_student,
                    "topic": topic
                }
            })

    except Exception as e:
        logger.error(f"Error in process_request: {e}")
        if not cancellation_token.ws_closed:
            await websocket.send_json({"type": "error", "data": {"message": str(e)}})


@app.websocket("/ws/dissertation_analysis")
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

###################################################HELPER FUNCTIONS###################################################
###################################################HELPER FUNCTIONS###################################################
###################################################HELPER FUNCTIONS###################################################

class WebSocketManager:
    def __init__(self, max_slots):
        self.active_users = 0
        self.max_slots = max_slots
        self.connections = {}

    def is_slot_available(self):
        return self.active_users < self.max_slots

    def increment_active_users(self):
        self.active_users += 1

    def decrement_active_users(self):
        if self.active_users > 0:
            self.active_users -= 1

    def add_websocket(self, user_id, websocket):
        self.connections[user_id] = websocket

    def remove_websocket(self, user_id):
        if user_id in self.connections:
            del self.connections[user_id]

    def get_websocket(self, user_id):
        return self.connections.get(user_id)


def resize_image(image_bytes: bytes, max_size: int = 800, min_size: int = 70) -> bytes:
    """
    Resize an image to ensure dimensions are between min_size and max_size while maintaining aspect ratio.
    
    Args:
        image_bytes: Original image bytes
        max_size: Maximum allowed size for any dimension
        min_size: Minimum allowed size for any dimension

    Returns:
        Resized image bytes
    """
    with Image.open(BytesIO(image_bytes)) as img:
        # Get original dimensions
        orig_width, orig_height = img.size
        
        # Calculate aspect ratio
        aspect_ratio = orig_width / orig_height

        # Check if image needs to be resized up or down
        needs_upscaling = orig_width < min_size or orig_height < min_size
        needs_downscaling = orig_width > max_size or orig_height > max_size

        if needs_upscaling:
            # If width is smaller than minimum, scale up maintaining aspect ratio
            if orig_width < min_size:
                new_width = min_size
                new_height = int(new_width / aspect_ratio)
                # If height is still too small, scale based on height instead
                if new_height < min_size:
                    new_height = min_size
                    new_width = int(new_height * aspect_ratio)
            else:
                new_height = min_size
                new_width = int(new_height * aspect_ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        elif needs_downscaling:
            # Use thumbnail for downscaling as it preserves aspect ratio
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Save the resized image
        output = BytesIO()
        img.save(output, format=img.format or 'PNG')  # Use PNG as fallback format
        return output.getvalue()

async def process_images_in_batch(
    images_data: List[Tuple[int, bytes]],
    batch_size: int = 10
) -> Dict[int, str]:
    """
    Process images in batches, resizing each image and sending them concurrently.
    Includes additional error handling and validation.

    Args:
        images_data: List of tuples containing (page_or_image_number, image_bytes)
        batch_size: Number of images to process in each batch

    Returns:
        Dictionary mapping page/image number to analysis result
    """
    ordered_results = {}

    for i in range(0, len(images_data), batch_size):
        batch = images_data[i:i + batch_size]

        try:
            # Resize images in the batch with minimum size requirement
            resized_batch = []
            for page_num, img_bytes in batch:
                try:
                    resized_img = resize_image(img_bytes, max_size=800, min_size=70)
                    resized_batch.append((page_num, resized_img))
                except Exception as e:
                    logger.error(f"Failed to resize image at page {page_num}: {e}")
                    continue

            # Skip batch if no images were successfully resized
            if not resized_batch:
                continue

            # Create async tasks for image analysis
            batch_tasks = [
                asyncio.create_task(analyze_image(img_bytes))
                for _, img_bytes in resized_batch
            ]

            # Run all tasks in the current batch concurrently
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Process results
            for (page_num, _), result in zip(resized_batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to analyze image at page {page_num}: {result}")
                    continue
                
                if isinstance(result, dict) and 'response' in result:
                    analysis_result = result['response'].strip()
                    if analysis_result:
                        ordered_results[page_num] = analysis_result

        except Exception as e:
            logger.error(f"Failed to process batch starting at index {i}: {e}")
            continue

    return dict(sorted(ordered_results.items()))



async def process_pdf(pdf_file: UploadFile) -> Dict[str, str]:
    """
    Process PDF file extracting text and images while preserving their original sequence.
    
    Args:
        pdf_file: Uploaded PDF file
    
    Returns:
        Dictionary with extracted text and image analyses in original sequence
    """
    pdf_bytes = await pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # Use a list to maintain order instead of OrderedDict
    final_elements = []
    images_data = []

    # Start image analysis from page 7
    image_analysis_start_page = 6  # Pages are zero-indexed, so page 7 is index 6

    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # Extract text using custom method for better block extraction
        page_text = extract_and_clean_text_from_page(page)
        if page_text:
            final_elements.append((page_num + 1, 'text', page_text))
        
        # Extract images from page, only analyze images starting from page 7
        if page_num >= image_analysis_start_page:
            for img_index, img in enumerate(page.get_images(full=True)):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    images_data.append((page_num + 1, image_bytes))
                except Exception as e:
                    logger.error(f"Failed to extract image on page {page_num + 1}: {e}")

    # Process images in batches
    image_analyses = await process_images_in_batch(images_data) if images_data else {}
    
    # Insert image analyses into the final_elements list in their original positions
    for page_num, analysis in image_analyses.items():
        # Find the index where we want to insert the image analysis
        insert_index = next(
            (i for i, (p, type_, _) in enumerate(final_elements) 
             if p == page_num and type_ == 'text'), 
            len(final_elements)
        )
        
        # Insert image analysis right after the corresponding text
        final_elements.insert(insert_index + 1, (page_num, 'image', analysis))

    doc.close()
    
    # Combine text and image analyses in order
    combined_text = []
    for page_num, content_type, content in final_elements:
        if content_type == 'text':
            combined_text.append(content)
        else:  # image
            combined_text.append(f"\n[Image Analysis on Page {page_num}]: {content}")

    return {"text_and_image_analysis": "\n".join(combined_text).strip()}


async def process_docx(docx_file: UploadFile):
    """
    Process a DOCX file with batch image processing.
    """
    docx_bytes = await docx_file.read()
    docx_stream = BytesIO(docx_bytes)
    document = Document(docx_stream)
    final_text = ""

    # Process text
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            cleaned_text = re.sub(r'\s+', ' ', text)
            final_text += f" {cleaned_text}"

    # Prepare images for batch processing
    images_data = []
    for idx, rel in enumerate(document.part.rels.values()):
        if isinstance(rel.target_part, ImagePart):
            try:
                images_data.append((idx, rel.target_part.blob))
            except Exception as e:
                logger.error(f"Failed to extract DOCX image {idx}: {e}")

    # Process images in batches
    if images_data:
        analysis_results = await process_images_in_batch(images_data)

        # Add results to final text
        for idx, analysis_result in sorted(analysis_results.items()):
            final_text += f"\n\nImage Analysis (Image {idx + 1}): {analysis_result}"
            
    cleaned_text = clean_text(final_text)
    return {"text_and_image_analysis": cleaned_text.strip()}


def extract_and_clean_text_from_page(page) -> str:
    """
    Extract and clean text from a PDF page using PyMuPDF.
    
    Args:
        page: PyMuPDF page object
    
    Returns:
        Cleaned text string
    """
    text_blocks = []
    blocks = page.get_text("blocks")
    for block in blocks:
        if isinstance(block[4], str) and block[4].strip():
            cleaned_block = ' '.join(block[4].split())
            if cleaned_block:
                text_blocks.append(cleaned_block)

    combined_text = ' '.join(text_blocks)
    return clean_text(combined_text)

def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing unnecessary elements.
    
    Args:
        text: Input text to clean
    
    Returns:
        Cleaned text string
    """
    import re
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Chapter\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\b(?!\s*[a-zA-Z])', '', text)
    text = re.sub(r'[\r\n\t\f]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


async def process_initial_agents(thesis_text: str) -> Dict[str, str]:
    """
    Process the initial set of agents concurrently in a batch.
    
    Args:
        thesis_text: The thesis text to analyze
        
    Returns:
        Dictionary containing results from all initial agents
    """
    # Create tasks for initial agents
    tasks = [
        extract_degree_agent(thesis_text),
        extract_name_agent(thesis_text),
        extract_topic_agent(thesis_text)
    ]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and handle any errors
    degree, name, topic = None, None, None
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Initial agent {i} failed with error: {result}")
            continue
            
        # Assign results based on index
        if i == 0:
            degree = result
        elif i == 1:
            name = result
        elif i == 2:
            topic = result
    
    return {
        "degree": degree or "Not found",
        "name": name or "Not found",
        "topic": topic or "Not found"
    }


class SimulatedWebSocket:
    def __init__(self, data, real_websocket=None):
        self.data = data  # Store initial data payload
        self.messages = asyncio.Queue()  # Queue for sent messages
        self.closed = False  # Status to track if WebSocket is closed
        self.real_websocket = real_websocket  # Optional disconnect handler

    async def receive_json(self):
        """
        Simulate receiving JSON data.
        """
        if self.closed:
            raise RuntimeError("WebSocket is closed.")
        if self.messages.qsize() == 0:
            # If no message is available, return the preloaded data
            return self.data
        else:
            # Wait for and return the next message in the queue
            return await self.messages.get()

    async def send_json(self, data):
        """
        Simulate sending JSON data, forwarding to the real WebSocket if provided.
        """
        if self.closed:
            raise RuntimeError("WebSocket is closed.")
        
        # Log message for debugging
        logger.info(f"Simulated WebSocket sending data: {data}")

        # Forward message to the actual WebSocket if it exists
        if self.real_websocket and not self.real_websocket.client_state.closed:
            await self.real_websocket.send_json(data)

        # Also enqueue the message locally (if needed for testing)
        await self.messages.put(data)

    async def close(self, code=1000, reason=""):
        """
        Simulate closing the WebSocket.
        """
        if self.closed:
            logger.warning("Simulated WebSocket is already closed.")
            return
        self.closed = True
        logger.info(f"Simulated WebSocket closed with code: {code}, reason: {reason}")

    @property
    def on_disconnect(self):
        return self._on_disconnect

    @on_disconnect.setter
    def on_disconnect(self, value):
        self._on_disconnect = value
        logger.info("Simulated WebSocket on_disconnect handler set.")

    async def simulate_disconnect(self):
        if self._on_disconnect:
            logger.info("Simulating WebSocket disconnection.")
            self._on_disconnect()
        self.closed = True
        if self.real_websocket:
            logger.info("Closing real WebSocket connection.")
            await self.real_websocket.close()


###################################################HELPER FUNCTIONS###################################################
###################################################HELPER FUNCTIONS###################################################
###################################################HELPER FUNCTIONS###################################################


def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)

if __name__ == "__main__":
    main()
