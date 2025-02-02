import os
import logging
from celery import Celery

# Logger setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Construct Redis URLs with password
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
BROKER_DB = os.getenv("REDIS_CELERY_BROKER_DB")
RESULT_DB = os.getenv("REDIS_CELERY_RESULT_DB")

# Redis URLs including authentication
CELERY_BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{BROKER_DB}"
CELERY_RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{RESULT_DB}"

# Create Celery app
celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["tasks"]
)

celery_app.conf.update(
    timezone="UTC",  # Set a timezone
    enable_utc=True,  # Enable UTC mode
    task_acks_late=True,  # Ensure tasks are acknowledged only after execution
    worker_prefetch_multiplier=1,  # Prevents one worker from grabbing too many tasks at once
    broker_heartbeat=30,  # Avoids long-running connections breaking
    broker_pool_limit=None,  # Prevents connection pool exhaustion
)