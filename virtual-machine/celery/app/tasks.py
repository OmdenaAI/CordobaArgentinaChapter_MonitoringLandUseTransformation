from celery.utils.log import get_task_logger
from celery_app import celery_app
from typing import Any, Dict
from time import sleep

logger = get_task_logger(__name__)

@celery_app.task
def square_number(n: int):
    return n ** 2

