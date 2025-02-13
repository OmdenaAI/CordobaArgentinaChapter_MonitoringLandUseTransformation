from fastapi import FastAPI, BackgroundTasks
from typing import Dict, Any
from celery import Celery
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
from celery.result import AsyncResult

import cv2
import uvicorn
import redis
import os
import logging

from cordobaDataPreprocessor import *


# Define a model for the input data
class InputData(BaseModel):
    inp_t1: str  
    inp_t2: str
    inp_long_from: float
    inp_long_to: float
    inp_lat_from: float
    inp_lat_to: float
    
    
# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Redis and Celery Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery('data_processing', broker=REDIS_URL, backend=REDIS_URL)

# Create Redis client
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Define a directory to store processed images
IMAGE_SAVE_DIR = "processed_images"
Path(IMAGE_SAVE_DIR).mkdir(parents=True, exist_ok=True)  # Ensure directory exists


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_data_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        logging.info(f"Processing data: {data}")
        inp_t1 = data.get("inp_t1")
        inp_t2 = data.get("inp_t2")
        inp_long_from = data.get("inp_long_from")
        inp_long_to = data.get("inp_long_to")
        inp_lat_from = data.get("inp_lat_from")
        inp_lat_to = data.get("inp_lat_to")
        preprocessor = CordobaDataPreprocessor()
        preprocessor.select_source(CordobaDataSource.AUTO)
        days = [inp_t1, inp_t2]
        area = LongLatBBox(
            float(inp_long_from),
            float(inp_long_to),
            float(inp_lat_from),
            float(inp_lat_to))
 
        logging.info(f"Area: {area}")
        images = preprocessor.get_satellite_data(days, area)
        # Save images and store their file paths
        image_paths = []
        for i, img in enumerate(images):
            img_rgb = img.to_rgb()  # Convert to RGB format
            filename = f"{IMAGE_SAVE_DIR}/satellite_{days[i]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            cv2.imwrite(filename, cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR))  # Save the image
            image_paths.append(filename)

        result = {"status": "processed", "image_paths": image_paths}
        return result
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise self.retry(exc=e)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/submit")
async def submit_data_processing_task(data: InputData, background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Receives an image file, enqueues a processing request, 
    and returns a task ID for status tracking.
    """
    task = process_data_task.delay(data=data.dict())
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
        print(task_result.result)
        return {"task_id": task_id, "result": task_result.result}
    return {"task_id": task_id, "message": "Task not completed yet"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
