from fastapi import FastAPI, Request
from typing import Dict, Any
from celery import Celery
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
from celery.result import AsyncResult
from fastapi.staticfiles import StaticFiles
from PIL import Image
import redis
import os
import logging

from app.service.cordobaPredictor import CordobaPredictor
from app.service.cordobaDataPreprocessor import CordobaDataPreprocessor, CordobaDataSource, LongLatBBox

# ---- Configuration ---- #
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize FastAPI
app = FastAPI()

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Celery Configuration
celery_app = Celery("change_detection", broker=REDIS_URL, backend=REDIS_URL)

# Redis Client
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Directories for saving images
IMAGE_SAVE_DIR = Path("processed_images")
OUTPUT_IMAGE_DIR = Path("output_images")
IMAGE_SAVE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# Mount Static Directories
app.mount("/output_images", StaticFiles(directory=OUTPUT_IMAGE_DIR), name="output_images")
app.mount("/processed_images", StaticFiles(directory=IMAGE_SAVE_DIR), name="processed_images")


# ---- Input Data Model ---- #
class InputData(BaseModel):
    inp_t1: str
    inp_t2: str
    inp_long_from: float
    inp_long_to: float
    inp_lat_from: float
    inp_lat_to: float


# ---- Celery Task ---- #
@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_change_detection_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task to process satellite image change detection.
    """
    try:
        logging.info(f"Processing data: {data}")
        
        # Extract Inputs
        payload = data["data"]
        base_url = data["base_url"]
        inp_t1, inp_t2 = payload["inp_t1"], payload["inp_t2"]
        inp_long_from, inp_long_to = payload["inp_long_from"], payload["inp_long_to"]
        inp_lat_from, inp_lat_to = payload["inp_lat_from"], payload["inp_lat_to"]

        # Prepare Processing Parameters
        preprocessor = CordobaDataPreprocessor()
        preprocessor.select_source(CordobaDataSource.AUTO)
        area = LongLatBBox(float(inp_long_from), float(inp_long_to), float(inp_lat_from), float(inp_lat_to))
        days = [inp_t1, inp_t2]
        
        logging.info(f"Fetching satellite images for area: {area} on days {days}")
        images = preprocessor.get_satellite_data(days, area)

        # Run Prediction
        logging.info(f"Prediction started for images: {days}")
        predictor = CordobaPredictor()
        prediction_image = predictor.predictPcaKMeanClustering([images[0], images[1]])

        # Save RGB Images & Prediction Result
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        rgb_filenames = [f"satellite_rgb_{day}_{timestamp}.png" for day in days]
        rgb_paths = [IMAGE_SAVE_DIR / filename for filename in rgb_filenames]

        for img, path in zip(images, rgb_paths):
            Image.fromarray(img.to_rgb(gamma=0.66)).save(path)

        prediction_filename = f"output_gray_{timestamp}.png"
        prediction_path = OUTPUT_IMAGE_DIR / prediction_filename
        Image.fromarray(prediction_image).save(prediction_path)

        # Generate complete URLs
        rgb_urls = [f"{base_url}/processed_images/{filename}" for filename in rgb_filenames]
        prediction_url = f"{base_url}/output_images/{prediction_filename}"

        logging.info("Change detection completed successfully.")

        return {"status": "processed", "rgb_urls": rgb_urls, "prediction_url": prediction_url}

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise self.retry(exc=e)


# ---- API Routes ---- #
@app.get("/")
async def root():
    """ Root endpoint to verify API is running """
    return {"message": "Hello World"}


@app.post("/submit")
async def submit_change_detection_task(request: Request, data: InputData) -> Dict[str, str]:
    """
    Receives data, enqueues a processing request, and returns a task ID.
    """
    base_url = f"{request.base_url.scheme}://{request.base_url.hostname}:{request.base_url.port}"
    task = process_change_detection_task.delay({"data": data.model_dump(), "base_url": base_url})
    return {"task_id": str(task.id)}


@app.get("/status/{task_id}")
def check_status(task_id: str) -> Dict[str, str]:
    """
    Checks the status of a Celery task by ID.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": task_result.status}


@app.get("/results/{task_id}")
def get_results(task_id: str) -> Dict:
    """
    Returns final results or output from the completed task.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.ready():
        return {"task_id": task_id, "result": task_result.result}
    return {"task_id": task_id, "message": "Task not completed yet"}
