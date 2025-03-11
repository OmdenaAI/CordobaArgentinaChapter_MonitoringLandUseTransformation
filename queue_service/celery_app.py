from celery import Celery

# Initialize Celery app
app = Celery(
    "queue_service",
    broker="redis://localhost:6379/0",  # Ensure Redis is running on this port
    backend="redis://localhost:6379/0"
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "queue_service.tasks.*": {"queue": "default"},
    },
    worker_concurrency="auto",  # Adjust based on server capacity
)

if __name__ == "__main__":
    celery_app.start()
