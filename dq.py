from locust import HttpUser, task, LoadTestShape, events
import gevent
import time
import os

class FileUploadUser(HttpUser):
    wait_time = None  # No wait time; controlled manually for precise timing

    @task
    def upload_pdf(self):
        # Submit a PDF file
        start_time = time.time()
        with open("resources/sample1.pdf", "rb") as f:
            self.client.post(
                "/upload",
                files={"file": ("sample1.pdf", f, "application/pdf")},
            )
        # Log the request duration (optional for debugging)
        response_time = time.time() - start_time
        print(f"Request completed in {response_time:.2f} seconds")


class ConstantRequestRateShape(LoadTestShape):
    """
    Custom load shape to maintain a constant request rate regardless of response time.
    Configurable via environment variables:
        - TARGET_RATE: Target request rate (requests per second)
        - RAMP_DURATION: Ramp-up duration in seconds
        - CONSTANT_DURATION: Duration of the constant phase in seconds
    """

    target_rate = float(os.getenv("TARGET_RATE", "5.0"))  # Target rate in requests/sec
    ramp_duration = int(os.getenv("RAMP_DURATION", "60"))  # Ramp-up duration in seconds
    constant_duration = int(os.getenv("CONSTANT_DURATION", "120"))  # Constant phase duration

    def tick(self):
        run_time = self.get_run_time()

        # Ramp-up phase: Increase rate linearly over time
        if run_time < self.ramp_duration:
            current_rate = (self.target_rate * (run_time / self.ramp_duration))
            return (current_rate, current_rate)

        # Constant phase: Maintain target rate
        if run_time < self.ramp_duration + self.constant_duration:
            return (self.target_rate, self.target_rate)

        # Stop the test after the constant phase
        return None


# Schedule requests independently of response times
@events.init.add_listener
def schedule_tasks(environment, **kwargs):
    """
    A separate thread ensures that requests are sent at fixed intervals
    regardless of response time.
    """
    target_rate = float(os.getenv("TARGET_RATE", "5.0"))
    interval = 1.0 / target_rate  # Time between requests (in seconds)

    def request_scheduler():
        while environment.runner.state in ["spawning", "running"]:
            environment.runner.start(user_count=1)
            gevent.sleep(interval)

    # Start the scheduler in a greenlet
    gevent.spawn(request_scheduler)
