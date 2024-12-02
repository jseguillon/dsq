from locust import HttpUser, task, between
import time
import threading
import random


class PostRequestInjector(HttpUser):
    wait_time = between(1, 1)  # Ensure no built-in waiting.
    
    @task
    def post_task(self):
        def make_request():
            """Simulates a long POST request with random sleep."""
            start_time = time.time()
            response = self.client.post(
                "/your-endpoint",
                json={"key": "value"},
                name="Simulated POST Request"
            )
            simulated_sleep = random.randint(30, 120)  # Simulate long sleep
            time.sleep(simulated_sleep)  # Mimic long processing time
            elapsed = time.time() - start_time
            print(f"Request completed in {elapsed} seconds")

        # Threaded task to run asynchronously
        threading.Thread(target=make_request).start()

    def on_start(self):
        """Initialize a rate-controlled task scheduler."""
        def schedule_requests():
            """Scheduler to inject 1.5 POST per second."""
            interval = 1 / 1.5  # 1.5 requests/sec means ~0.67 seconds between requests.
            while True:
                self.post_task()
                time.sleep(interval)

        # Start the scheduler in a separate thread
        threading.Thread(target=schedule_requests, daemon=True).start()
