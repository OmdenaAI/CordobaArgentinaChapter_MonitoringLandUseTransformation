from celery import Celery

# Initialize Celery app
celery_app = Celery(
    "queue_service",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_retries=3,
    task_retry_delay=10,
    task_routes={
        "queue_service.tasks.*": {"queue": "default"},
    },
    worker_concurrency="auto",
)

if __name__ == "__main__":
    celery_app.start()
