from celery_app import celery_app, logger
from typing import Any, Dict
from time import sleep

@celery_app.task
def square_number(n: int):
    return n ** 2