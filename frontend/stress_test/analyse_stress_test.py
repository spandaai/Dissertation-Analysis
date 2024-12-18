import asyncio
import websockets
import json
import time
import statistics
import logging
import random
from typing import Dict, Any
from analyzed_data import pre_analysis_data
from rubric import rubric

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketStressTester:
    def __init__(
        self, 
        websocket_url: str, 
        concurrent_users: int = 20, 
        requests_per_user: int = 1
    ):
        self.websocket_url = websocket_url
        self.concurrent_users = concurrent_users
        self.requests_per_user = requests_per_user
        
        # Metrics tracking
        self.response_times = []
        self.success_count = 0
        self.failure_count = 0
        self.error_details = []


    async def send_single_request(self, user_id: int, request_id: int):
        """Send a single WebSocket request and track performance."""
        start_time = time.time()
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Send dissertation data
                    await websocket.send(json.dumps({
            "pre_analysis": pre_analysis_data,
            "rubric": rubric,
            "feedback": "Please provide constructive feedback based on evaluation."
        }))

                # Process response
                while True:
                    message = await websocket.recv()
                    message_data = json.loads(message)
                    
                    if message_data.get("type") in ["complete", "error"]:
                        break

                elapsed_time = time.time() - start_time
                self.response_times.append(elapsed_time)
                self.success_count += 1
                logger.debug(f"User {user_id} - Request {request_id}: Success ({elapsed_time:.2f}s)")

        except Exception as e:
            self.failure_count += 1
            error_msg = f"User {user_id} - Request {request_id}: Exception - {str(e)}"
            self.error_details.append(error_msg)
            logger.error(error_msg)

    async def simulate_user(self, user_id: int):
        """Simulate a user sending multiple requests."""
        tasks = [
            self.send_single_request(user_id, i) 
            for i in range(self.requests_per_user)
        ]
        await asyncio.gather(*tasks)

    async def run_stress_test(self):
        """Execute the full stress test."""
        logger.info(f"Starting WebSocket stress test with {self.concurrent_users} concurrent users, "
                    f"{self.requests_per_user} requests per user")
        
        start_time = time.time()
        tasks = [self.simulate_user(i) for i in range(self.concurrent_users)]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        self.print_results(total_time)

    def print_results(self, total_time: float):
        """Print comprehensive stress test results."""
        total_requests = self.concurrent_users * self.requests_per_user
        success_rate = (self.success_count / total_requests) * 100
        
        logger.info("\n=== WebSocket Stress Test Results ===")
        logger.info(f"Total Requests: {total_requests}")
        logger.info(f"Successful Requests: {self.success_count}")
        logger.info(f"Failed Requests: {self.failure_count}")
        logger.info(f"Success Rate: {success_rate:.2f}%")
        logger.info(f"Total Test Duration: {total_time:.2f} seconds")
        
        if self.response_times:
            logger.info(f"Average Response Time: {statistics.mean(self.response_times):.2f} seconds")
            logger.info(f"Median Response Time: {statistics.median(self.response_times):.2f} seconds")
            logger.info(f"Min Response Time: {min(self.response_times):.2f} seconds")
            logger.info(f"Max Response Time: {max(self.response_times):.2f} seconds")
            
        if self.error_details:
            logger.info("\nError Details:")
            for error in self.error_details[:10]:
                logger.info(error)
            if len(self.error_details) > 10:
                logger.info(f"... and {len(self.error_details) - 10} more errors")

def main():
    # Configuration
    WEBSOCKET_URL = "ws://172.16.92.136/ws/dissertation_analysis"
    CONCURRENT_USERS = 0
    REQUESTS_PER_USER = 1

    # Create and run stress tester
    stress_tester = WebSocketStressTester(
        WEBSOCKET_URL,
        CONCURRENT_USERS,
        REQUESTS_PER_USER
    )

    asyncio.run(stress_tester.run_stress_test())

if __name__ == "__main__":
    main()