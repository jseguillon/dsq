from locust import HttpUser, task, LoadTestShape, events
import gevent
import time
import os

class FileUploadUser(HttpUser):
    """
    A user class for file upload testing.
    Tasks are controlled externally for precise timing.
    """
    wait_time = None  # No automatic waiting; timing is controlled manually

    @task
    def upload_pdf(self):
        # Submit a PDF file
        with open("resources/sample1.pdf", "rb") as f:
            self.client.post(
                "/upload",
                files={"file": ("sample1.pdf", f, "application/pdf")},
            )


class StableRateLoadShape(LoadTestShape):
    """
    A load shape to maintain a stable request rate, irrespective of response times.
    Configurable via environment variables:
        - TARGET_RATE: Target request rate (requests per second)
        - RAMP_DURATION: Ramp-up duration in seconds
        - CONSTANT_DURATION: Duration of the constant rate phase
    """

    target_rate = float(os.getenv("TARGET_RATE", "6.0"))  # Target requests per second
    ramp_duration = int(os.getenv("RAMP_DURATION", "60"))  # Ramp-up duration in seconds
    constant_duration = int(os.getenv("CONSTANT_DURATION", "120"))  # Constant phase duration

    def tick(self):
        run_time = self.get_run_time()

        # Ramp-up phase
        if run_time < self.ramp_duration:
            # Linearly increase the rate
            current_rate = self.target_rate * (run_time / self.ramp_duration)
            return (current_rate, current_rate)

        # Constant phase
        if run_time < self.ramp_duration + self.constant_duration:
            return (self.target_rate, self.target_rate)

        # Stop the test after the constant phase
        return None


@events.init.add_listener
def schedule_requests(environment, **kwargs):
    """
    A scheduler that sends requests at precise intervals to maintain a constant rate.
    """
    target_rate = float(os.getenv("TARGET_RATE", "6.0"))
    interval = 1.0 / target_rate  # Time between requests (in seconds)

    def send_requests():
        while environment.runner.state in ["spawning", "running"]:
            start_time = time.time()

            # Spawn a user to execute the task
            environment.runner.start(user_count=1)

            # Sleep to maintain the target interval
            elapsed = time.time() - start_time
            sleep_time = max(0, interval - elapsed)
            gevent.sleep(sleep_time)

    # Start the scheduler in a greenlet
    gevent.spawn(send_requests)
