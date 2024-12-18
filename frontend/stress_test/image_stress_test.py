import asyncio
import aiohttp
import time
from pathlib import Path
import statistics
import logging
from tqdm import tqdm
from datetime import datetime
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
class APIStressTester:
    def __init__(self, endpoint_url, test_file_path, concurrent_users=10, requests_per_user=50):
        self.endpoint_url = endpoint_url
        self.test_file_path = Path(test_file_path)
        self.concurrent_users = concurrent_users
        self.requests_per_user = requests_per_user
        self.response_times = []
        self.success_count = 0
        self.failure_count = 0
        self.error_details = []
    async def send_single_request(self, session, user_id, request_id, progress_bar):
        """Sends a single request and tracks its performance."""
        start_time = time.time()
        try:
            logger.debug(f"User {user_id} - Request {request_id}: Preparing to send request")
            with open(self.test_file_path, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('file', f, filename=self.test_file_path.name, content_type='application/pdf')
                async with session.post(self.endpoint_url, data=form_data) as response:
                    elapsed_time = time.time() - start_time
                    self.response_times.append(elapsed_time)
                    if response.status == 200:
                        self.success_count += 1
                        logger.info(
                            f"User {user_id} - Request {request_id}: Success "
                            f"(Response: {response.status}, Time: {elapsed_time:.2f}s)"
                        )
                    else:
                        self.failure_count += 1
                        error_msg = f"User {user_id} - Request {request_id}: Failed (Status: {response.status})"
                        self.error_details.append(error_msg)
                        logger.error(error_msg)
        except Exception as e:
            self.failure_count += 1
            error_msg = f"User {user_id} - Request {request_id}: Exception - {str(e)}"
            self.error_details.append(error_msg)
            logger.error(error_msg)
        finally:
            progress_bar.update(1)
    async def simulate_user(self, user_id, progress_bar):
        """Simulates a user by sending multiple requests."""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.send_single_request(session, user_id, i, progress_bar)
                for i in range(self.requests_per_user)
            ]
            await asyncio.gather(*tasks)
    async def run_stress_test(self):
        """Runs the stress test with concurrent users."""
        logger.info(f"Starting stress test with {self.concurrent_users} users, "
                    f"{self.requests_per_user} requests per user.")
        total_requests = self.concurrent_users * self.requests_per_user
        logger.info(f"Total requests to be sent: {total_requests}")
        start_time = time.time()
        with tqdm(total=total_requests, desc="Processing Requests", ncols=100) as progress_bar:
            tasks = [
                self.simulate_user(user_id, progress_bar)
                for user_id in range(self.concurrent_users)
            ]
            await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        self.print_results(total_time)
    def print_results(self, total_time):
        """Prints the results of the stress test."""
        total_requests = self.concurrent_users * self.requests_per_user
        success_rate = (self.success_count / total_requests) * 100
        logger.info("\n=== Stress Test Results ===")
        logger.info(f"Total Requests: {total_requests}")
        logger.info(f"Successful Requests: {self.success_count}")
        logger.info(f"Failed Requests: {self.failure_count}")
        logger.info(f"Success Rate: {success_rate:.2f}%")
        logger.info(f"Total Test Duration: {total_time:.2f} seconds")
        if self.response_times:
            logger.info(f"Average Request Time: {statistics.mean(self.response_times):.2f} seconds")
            logger.info(f"Median Request Time: {statistics.median(self.response_times):.2f} seconds")
            logger.info(f"Min Request Time: {min(self.response_times):.2f} seconds")
            logger.info(f"Max Request Time: {max(self.response_times):.2f} seconds")
        if self.error_details:
            logger.error("\nError Details:")
            for error in self.error_details[:10]:  # Show first 10 errors
                logger.error(error)
            if len(self.error_details) > 10:
                logger.error(f"... and {len(self.error_details) - 10} more errors")
def main():
    # Configuration
    API_ENDPOINT = "http://172.16.92.136/api/extract_text_from_file_and_analyze_images"
    TEST_FILE_PATH = "manan.pdf"
    CONCURRENT_USERS = 100
    REQUESTS_PER_USER = 1
    logger.info("Initializing API Stress Tester")
    logger.info(f"Endpoint: {API_ENDPOINT}")
    logger.info(f"Test File: {TEST_FILE_PATH}")
    logger.info(f"Concurrent Users: {CONCURRENT_USERS}")
    logger.info(f"Requests per User: {REQUESTS_PER_USER}")
    # Create and run stress tester
    stress_tester = APIStressTester(
        API_ENDPOINT, TEST_FILE_PATH, CONCURRENT_USERS, REQUESTS_PER_USER
    )
    asyncio.run(stress_tester.run_stress_test())
if __name__ == "__main__":
    main()