import asyncio
import aiohttp
import time
import statistics
import logging
from datetime import datetime
from tqdm.asyncio import tqdm
from long_text import thesis_text
from rubric import rubric
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
class PreAnalysisStressTester:
    def __init__(self, endpoint_url, concurrent_users=10, requests_per_user=50):
        self.endpoint_url = endpoint_url
        self.concurrent_users = concurrent_users
        self.requests_per_user = requests_per_user
        self.response_times = []
        self.success_count = 0
        self.failure_count = 0
        self.error_details = []
    def generate_test_data(self):
        return {
            "thesis": thesis_text,
            "rubric": rubric
        }
    async def send_single_request(self, session, user_id, request_id, progress_bar):
        start_time = time.time()
        try:
            request_data = self.generate_test_data()
            async with session.post(self.endpoint_url, json=request_data) as response:
                await response.text()
                elapsed_time = time.time() - start_time
                self.response_times.append(elapsed_time)
                if response.status == 200:
                    self.success_count += 1
                    logger.debug(f"User {user_id} - Request {request_id}: Success ({elapsed_time:.2f}s)")
                else:
                    self.failure_count += 1
                    error_msg = f"User {user_id} - Request {request_id}: Failed with status {response.status}"
                    self.error_details.append(error_msg)
                    logger.error(error_msg)
        except Exception as e:
            self.failure_count += 1
            error_msg = f"User {user_id} - Request {request_id}: Exception - {str(e)}"
            self.error_details.append(error_msg)
            logger.error(error_msg)
        finally:
            progress_bar.update(1)  # Update the progress bar
    async def simulate_user(self, user_id, progress_bar):
        async with aiohttp.ClientSession() as session:
            tasks = [self.send_single_request(session, user_id, i, progress_bar)
                     for i in range(self.requests_per_user)]
            await asyncio.gather(*tasks)
    async def run_stress_test(self):
        logger.info(f"Starting stress test with {self.concurrent_users} concurrent users, "
                    f"{self.requests_per_user} requests per user.")
        total_requests = self.concurrent_users * self.requests_per_user
        logger.info(f"Total requests to be sent: {total_requests}")
        # Create a progress bar
        with tqdm(total=total_requests, desc="Processing Requests", unit="req") as progress_bar:
            tasks = [self.simulate_user(i, progress_bar) for i in range(self.concurrent_users)]
            start_time = time.time()
            await asyncio.gather(*tasks)
            total_time = time.time() - start_time
        self.print_results(total_time)
    def print_results(self, total_time):
        total_requests = self.concurrent_users * self.requests_per_user
        success_rate = (self.success_count / total_requests) * 100
        logger.info("\n=== Stress Test Results ===")
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
            for error in self.error_details[:10]:  # Show first 10 errors
                logger.info(error)
            if len(self.error_details) > 10:
                logger.info(f"... and {len(self.error_details) - 10} more errors")
def main():
    # Configuration
    API_ENDPOINT = "http://172.16.92.136/api/pre_analyze"
    CONCURRENT_USERS = 100
    REQUESTS_PER_USER = 1
    # Create and run stress tester
    stress_tester = PreAnalysisStressTester(
        API_ENDPOINT,
        CONCURRENT_USERS,
        REQUESTS_PER_USER
    )
    asyncio.run(stress_tester.run_stress_test())
if __name__ == "__main__":
    main()