"""
Kafka Queue Management Module

This module handles Kafka queue operations for dissertation analysis requests with 
concurrent user management. Primarily focused on Kafka producer/consumer setup and 
message handling.

Core Functionality:
- Kafka message queue management (producer/consumer)
- WebSocket connection handling for frontend communication
- Concurrent user count management
- Topic creation and management

Configuration:
- Uses environment variables for Kafka and database settings
- Configurable max concurrent users (default: 3)
- Default Kafka topic: 'dissertation_analysis_queue'

Key Components:
- Producer: Single Kafka producer instance for enqueueing requests
- Consumer: Single consumer instance for processing queued messages
- WebSocket: Manages frontend notification and reconnection
- User tracking: Global counter with locks for concurrent access

Dependencies:
- aiokafka: For async Kafka operations 
- kafka-python: For admin operations
- asyncio: For concurrent operations

Note: This is a utility module focused purely on Kafka queue management and 
should be used in conjunction with the main dissertation analysis system.
"""

import os
import asyncio
import logging 
import json

from dissertation_analysis.domain.ExampleWorkflowWithKafka.types import QueryRequestThesisAndRubric
from dissertation_analysis.domain.FunctionalBlocks.AnalysisAlgorithms.analysis_algorithms import DissertationAnalyzer

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer, TopicPartition, OffsetAndMetadata # type: ignore
from kafka.admin import KafkaAdminClient, NewTopic # type: ignore
from aiokafka.admin import NewTopic # type: ignore
from aiokafka import AIOKafkaProducer # type: ignore


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  


SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "dissertation_analysis_queue")
current_users = 0
MAX_CONCURRENT_USERS = int(os.getenv("MAX_CONCURRENT_USERS", 3))

producer = None
queue_lock = asyncio.Lock()
user_lock = asyncio.Lock()

consumer_initialized = False
consumer_lock = asyncio.Lock()
consumer = None  # Single consumer instance
notification_clients = {}  # Map of session IDs to WebSocket connections
connected_websockets = {}
producer = None  # Single producer instance
consumer_task = None  # Single consumer task
    
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


async def process_dequeued_request(data: dict, session_id: str):
    """
    Process a dequeued Kafka request using a reconnected WebSocket.
    """
    try:
        # Notify the frontend to reconnect
        await notify_frontend_to_reconnect(session_id)

        # Wait for the frontend to reconnect
        websocket = await wait_for_websocket_reconnect(session_id)

        # Create analyzer instance and process the request
        analyzer = DissertationAnalyzer()
        request = QueryRequestThesisAndRubric(**data)
        
        try:
            await analyzer.process_dissertation(websocket, request)
        except Exception as e:
            logger.error(f"Error during dissertation analysis: {e}")
            if not analyzer.is_connection_closed:
                await analyzer.safe_send(websocket, {
                    "type": "error",
                    "data": {
                        "message": f"Analysis error: {str(e)}"
                    }
                })
            
        # Handle WebSocket cleanup
        if websocket:
            try:
                await analyzer.handle_disconnect()
            except Exception as e:
                logger.error(f"Error during WebSocket cleanup: {e}")

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

