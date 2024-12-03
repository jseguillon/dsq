from locust import HttpUser, task, events
import time
import threading


class SteadyRateUser(HttpUser):
    """
    A Locust user that generates POST requests at a steady rate.
    Supports fractional target rates per user (e.g., 0.2 requests/sec).
    """
    target_rate_per_user = 0.2  # Requests per second (e.g., 1 request every 5 seconds)

    def on_start(self):
        """
        Initialize user-specific variables and start the scheduler thread.
        """
        self.last_request_time = time.time()
        self.lock = threading.Lock()
        self.scheduler_thread = threading.Thread(target=self.scheduler, daemon=True)
        self.scheduler_thread.start()

    def scheduler(self):
        """
        Schedule tasks at the target rate, including support for low request rates.
        """
        interval = 1 / self.target_rate_per_user  # Time interval between requests
        while True:
            now = time.time()
            time_since_last = now - self.last_request_time
            sleep_time = max(0, interval - time_since_last)
            time.sleep(sleep_time)

            with self.lock:
                self.last_request_time = time.time()
                # Directly call the task
                self.run_task(self.post_task)

    def run_task(self, task_func):
        """
        Executes a given task while respecting Locust's internal mechanisms.
        """
        task_func()

    @task
    def post_task(self):
        """
        The actual POST request logic.
        """
        start_time = time.time()
        try:
            response = self.client.post("/endpoint", json={"key": "value"})
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            if response.status_code == 200:
                # Report success
                events.request_success.fire(
                    request_type="POST",
                    name="/endpoint",
                    response_time=response_time,
                    response_length=len(response.content),
                )
            else:
                # Report failure
                events.request_failure.fire(
                    request_type="POST",
                    name="/endpoint",
                    response_time=response_time,
                    exception=Exception(f"Unexpected status code {response.status_code}"),
                )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            events.request_failure.fire(
                request_type="POST",
                name="/endpoint",
                response_time=response_time,
                exception=e,
            )
