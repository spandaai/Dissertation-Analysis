"""
Configuration and WebSocket Management Module

This module provides core configuration management and WebSocket simulation capabilities for a 
distributed LLM-based system. It implements:

1. WebSocket Connection Management:
   - Tracks and limits concurrent user connections
   - Manages WebSocket connection lifecycle
   - Provides connection pooling and user tracking

2. Model Configuration:
   - Supports dual deployment with VLLM and Ollama
   - Configures different model types for various tasks:
     * Analysis
     * Extraction
     * Summary
     * Image Processing
     * Scoring
   - Implements fallback logic between VLLM and Ollama

3. Environment Configuration:
   - Loads and manages environment variables for model endpoints
   - Provides URL configuration for different model services
   - Implements availability checking for different model backends

4. WebSocket Simulation (for testing):
   - Simulates WebSocket behavior for testing purposes
   - Supports message queuing and forwarding
   - Handles connection state management
   - Provides disconnect simulation capabilities

Technical Components:
- Enum-based model and URL type management
- Asynchronous WebSocket implementation
- Environment variable based configuration
- Queue-based message handling for simulation
- Logging integration for debugging and monitoring

The system supports flexible deployment configurations with:
- Multiple model backend options (VLLM/Ollama)
- Different model types for specialized tasks
- Concurrent connection management
- Graceful fallback mechanisms
"""

import os
from enum import Enum
from typing import Optional
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class ModelType(Enum):
    ANALYSIS = "ANALYSIS"
    EXTRACTION = "EXTRACTION"
    SUMMARY = "SUMMARY"
    IMAGE = "IMAGE"
    SCORING = "SCORING"

class UrlType(Enum):
    ANALYSIS = "ANALYSIS"
    EXTRACTION = "EXTRACTION"
    SUMMARY = "SUMMARY"
    IMAGE = "IMAGE"
    SCORING = "SCORING"

class EnvConfig:
    def __init__(self):
        # VLLM Configuration
        self.vllm_url = os.getenv("VLLM_MODEL_FOR_ANALYSIS")
        self.vllm_models = {
            ModelType.ANALYSIS: os.getenv("VLLM_MODEL_FOR_ANALYSIS"),
            ModelType.EXTRACTION: os.getenv("VLLM_MODEL_FOR_EXTRACTION"),
            ModelType.SUMMARY: os.getenv("VLLM_MODEL_FOR_SUMMARY"),
            ModelType.IMAGE: os.getenv("VLLM_MODEL_FOR_IMAGE"),
            ModelType.SCORING: os.getenv("VLLM_MODEL_FOR_SCORING"),
        }
        self.vllm_urls = {
            UrlType.ANALYSIS: os.getenv("VLLM_URL_FOR_ANALYSIS"),
            UrlType.EXTRACTION: os.getenv("VLLM_URL_FOR_EXTRACTION"),
            UrlType.SUMMARY: os.getenv("VLLM_URL_FOR_SUMMARY"),
            UrlType.IMAGE: os.getenv("VLLM_URL_FOR_IMAGE"),
            UrlType.SCORING: os.getenv("VLLM_URL_FOR_SCORING"),
        }
        
        # Ollama Configuration
        self.ollama_url = os.getenv("OLLAMA_URL")
        self.ollama_models = {
            ModelType.ANALYSIS: os.getenv("OLLAMA_MODEL_FOR_ANALYSIS"),
            ModelType.EXTRACTION: os.getenv("OLLAMA_MODEL_FOR_EXTRACTION"),
            ModelType.SUMMARY: os.getenv("OLLAMA_MODEL_FOR_SUMMARY"),
            ModelType.IMAGE: os.getenv("OLLAMA_MODEL_FOR_IMAGE"),
            ModelType.SCORING: os.getenv("OLLAMA_MODEL_FOR_SCORING"),
        }
    
    def is_vllm_available(self, model_type: ModelType) -> bool:
        """Check if VLLM is configured and available for specific model type"""
        url_type = UrlType[model_type.value]  # Convert ModelType to corresponding UrlType
        return bool(self.vllm_urls.get(url_type) and self.vllm_models.get(model_type))
    
    def is_ollama_available(self, model_type: ModelType) -> bool:
        """Check if Ollama is configured and available for specific model type"""
        return bool(self.ollama_url and self.ollama_models.get(model_type))
    
    def get_model_and_url(self, model_type: ModelType) -> tuple[Optional[str], Optional[str]]:
        """Get the appropriate model and URL based on availability"""
        # First try VLLM
        if self.is_vllm_available(model_type):
            url_type = UrlType[model_type.value]  # Convert ModelType to corresponding UrlType
            return self.vllm_models[model_type], self.vllm_urls[url_type]
        # Then try Ollama
        elif self.is_ollama_available(model_type):
            return self.ollama_models[model_type], self.ollama_url
        return None, None



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