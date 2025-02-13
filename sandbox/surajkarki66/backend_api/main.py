from fastapi import FastAPI, UploadFile, BackgroundTasks
from typing import Dict, Any
from celery import Celery
from celery.result import AsyncResult

import uvicorn
import redis
import os
import logging

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Redis and Celery Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery('image_processing', broker=REDIS_URL, backend=REDIS_URL)

# Create Redis client
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_image_task(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        logging.info(f"Processing image: {image_data}")
        # Placeholder for actual image processing logic
        result = {"status": "processed", "details": image_data}
        return result
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise self.retry(exc=e)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/submit")
async def submit_image_task(file: UploadFile, background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Receives an image file, enqueues a processing request, 
    and returns a task ID for status tracking.
    """
    image_data = {"filename": file.filename}
    task = process_image_task.delay(image_data=image_data)
    return {"task_id": str(task.id)}

@app.get("/status/{task_id}")
def check_status(task_id: str) -> Dict[str, str]:
    """
    Checks the current status of a Celery task by ID.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": task_result.status}

@app.get("/results/{task_id}")
def get_results(task_id: str) -> Dict:
    """
    Returns the final results or any output data from the completed task.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.ready():
        return {"task_id": task_id, "result": task_result.result}
    return {"task_id": task_id, "message": "Task not completed yet"}

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
