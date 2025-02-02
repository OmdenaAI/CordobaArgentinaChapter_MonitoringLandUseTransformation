import os
from celery import Celery

# Construct Redis URLs with password
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
BROKER_DB = os.getenv("REDIS_CELERY_BROKER_DB")
RESULT_DB = os.getenv("REDIS_CELERY_RESULT_DB")

# Redis URLs including authentication
CELERY_BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{BROKER_DB}"
CELERY_RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{RESULT_DB}"

# Connect to Celery
celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)
