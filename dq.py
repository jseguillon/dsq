from locust import HttpUser, task, between
import gevent
import time

class SteadyRateUser(HttpUser):
    wait_time = between(0, 0)  # No wait time; rate is controlled manually
    target_rate = 1.5  # Target requests per second

    def on_start(self):
        """Start the green thread for injecting tasks at a steady rate."""
        gevent.spawn(self.task_injector)

    def task_injector(self):
        """Injects tasks at a fixed rate using gevent."""
        interval = 1 / self.target_rate
        while True:
            start_time = time.time()
            
            # Schedule the POST task
            self.schedule_task(self.post_task)
            
            # Wait for the remainder of the interval
            elapsed = time.time() - start_time
            gevent.sleep(max(0, interval - elapsed))

    def schedule_task(self, task_function):
        """Injects a task into Locust's task queue."""
        self._task_queue.put_nowait(task_function)

    @task
    def post_task(self):
        """The actual POST request logic."""
        response = self.client.post("/endpoint", json={"key": "value"})
        if response.status_code != 200:
            self.environment.events.request_failure.fire(
                request_type="POST",
                name="/endpoint",
                response_time=0,  # Replace with the measured response time
                exception=Exception("Request failed"),
            )
        else:
            self.environment.events.request_success.fire(
                request_type="POST",
                name="/endpoint",
                response_time=0,  # Replace with the measured response time
                response_length=len(response.content),
            )
