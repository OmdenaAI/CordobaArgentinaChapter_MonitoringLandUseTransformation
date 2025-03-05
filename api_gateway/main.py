from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from celery import Celery
from typing import Dict, List
from celery.result import AsyncResult
from queue_service.tasks import *
from pydantic import BaseModel, Field
from datetime import date
from rate_limit.rate_limiter import RateLimitFactory
from rate_limit.limiting_algorithms import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChangeDetectionRequest(BaseModel):
    """
    Pydantic model for change detection request.

    Constructor for an instance of CordobaImage.
    date: the acquisition date and time (eg. "2022-12-01T00:01")
    area: the bounding longitudes and latitudes of the image
    resolution: the size in meter of one pixel
    width, height: dimensions of the image
    """
    gee_account: str = Field(..., description="Google Earth Engine account ID")
    gee_credentials_path: str = Field(..., description="Path to Google Earth Engine credentials file")
    date: str = Field(..., description="Acquisition date and time (eg. '2022-12-01T00:01')")
    area: LongLatBBox = Field(..., description="Bounding longitudes and latitudes of the image")
    resolution: float = Field(..., description="Size in meter of one pixel")
    width: int = Field(..., description="Width of the image")
    height: int = Field(..., description="Height of the image")


    class Config:
        json_schema_extra = {
            "example": {
                "gee_account": "cordoba-team",
                "gee_credentials_path": "/path/to/credentials.json",
                "date": "2022-12-01T00:01",
                "area": {
                    "longitude_min": -122.5,
                    "latitude_min": 37.5,
                    "longitude_max": -122.4,
                    "latitude_max": 37.6
                },
                "resolution": 30,
                "width": 256,
                "height": 256
            }
        }

# Initialize FastAPI app
app = FastAPI(
    title=settings.CORDOBA_API_TITLE,
    description=settings.CORDOBA_API_DESCRIPTION,
    version=settings.CORDOBA_API_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
We are tracking API limit from every IP address and 
This way we can handle traffic from each end user independently.
"""
ip_addresses = {}

"""
We have two endpoints in the API, one is limited and the other is unlimited.

The limited endpoint is rate-limited using the TokenBucket algorithm 
which can be changed to any other algorithm by passing the algorithm name 
as a parameter to the get_instance method of the RateLimitFactory class.
"""
@app.get("/limited")
def limited(request: Request):
    client = request.client.host
    try:
        if client not in ip_addresses:
            ip_addresses[client] = RateLimitFactory.get_instance("TokenBucket")
        if ip_addresses[client].allow_request():
            return "This is a limited use API"
    except RateLimitExceeded as e:
        raise e

"""
The unlimited endpoint is not rate-limited and can be accessed without any restrictions.
"""
@app.get("/unlimited")
def unlimited(request: Request):
    return "Free to use API limitless"

# Initialize Celery app
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# Basic health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint to verify the API is running.
    """
    try:
        celery_status = celery_app.control.ping()  # Check Celery worker status
        return {"status": "healthy", "service": "land-use-change-api", "celery_status": celery_status}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}

# Submit a request to process an image for change detection
@app.post("/process")
async def process_change_detection(request: ChangeDetectionRequest) -> Dict[str, str]:
    """
    Submit a change detection request for processing.
    Returns a task ID that can be used to check the status of the task.
    """
    try:
        logging.info(f"Processing change detection for account: {request.gee_account}")

        # Convert request to a dictionary that can be used by Celery tasks
        task_data = request.model_dump()

        # Submit task to Celery
        task = celery_app.send_task("tasks.process_image_task", args=[task_data])
        logging.info(f"Task submitted with ID: {task.id}")
        return {"task_id": task.id, "status": "submitted"}

    except Exception as e:
        logging.error(f"Error processing change detection: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.post("/preprocess-ndvi")
async def preprocess_ndvi(request: ChangeDetectionRequest) -> Dict[str, str]:
    """
    Submit a request for NDVI preprocessing.
    Returns a task ID that can be used to check the status of the task.
    """
    try:
        logging.info(f"Processing NDVI for account: {request.gee_account}")

        # Convert request to dictionary for Celery task
        task_data = request.dict()

        # Submit task to Celery
        task = celery_app.send_task("tasks.preprocess_ndvi_task", args=[task_data])
        logging.info(f"NDVI preprocessing task submitted with ID: {task.id}")
        return {"task_id": task.id, "status": "submitted"}

    except Exception as e:
        logging.error(f"Error processing NDVI: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.post("/preprocess-ndbi")
async def preprocess_ndbi(request: ChangeDetectionRequest) -> Dict[str, str]:
    """
    Submit a request for NDBI preprocessing.
    Returns a task ID that can be used to check the status of the task.
    """
    try:
        logging.info(f"Processing NDBI for account: {request.gee_account}")

        # Convert request to dictionary for Celery task
        task_data = request.dict()

        # Submit task to Celery
        task = celery_app.send_task("tasks.preprocess_ndbi_task", args=[task_data])
        logging.info(f"NDBI preprocessing task submitted with ID: {task.id}")
        return {"task_id": task.id, "status": "submitted"}

    except Exception as e:
        logging.error(f"Error processing NDBI: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.post("/preprocess-evi")
async def preprocess_evi(request: ChangeDetectionRequest) -> Dict[str, str]:
    """
    Submit a request for EVI preprocessing.
    Returns a task ID that can be used to check the status of the task.
    """
    try:
        logging.info(f"Processing EVI for account: {request.gee_account}")

        # Convert request to dictionary for Celery task
        task_data = request.dict()

        # Submit task to Celery
        task = celery_app.send_task("tasks.preprocess_evi_task", args=[task_data])
        logging.info(f"EVI preprocessing task submitted with ID: {task.id}")
        return {"task_id": task.id, "status": "submitted"}

    except Exception as e:
        logging.error(f"Error processing EVI: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.post("/get-best-acquisition-dates")
async def get_best_acquisition_dates(request: ChangeDetectionRequest) -> Dict[str, str]:
    """
    Get best acquisition dates based on the provided date range and area.
    Returns a task ID that can be used to check the status of the task.
    """
    try:
        logging.info(f"Getting best acquisition dates for account: {request.gee_account}")

        # Convert request to dictionary for Celery task
        task_data = request.model_dump()

        # Submit task to Celery
        task = celery_app.send_task("tasks.get_best_acquisition_dates_task", args=[task_data])
        logging.info(f"Best acquisition dates task submitted with ID: {task.id}")
        return {"task_id": task.id, "status": "submitted"}

    except Exception as e:
        logging.error(f"Error getting best acquisition dates: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, str]:
    """
    Get the status of a specific Celery task.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.state == 'PENDING':
            return {"task_id": task_id, "status": "pending"}
        elif task_result.state == 'SUCCESS':
            return {"task_id": task_id, "status": "completed", "result": task_result.result}
        elif task_result.state == 'FAILURE':
            return {"task_id": task_id, "status": "failed", "error": str(task_result.result)}
        else:
            return {"task_id": task_id, "status": task_result.state}

    except Exception as e:
        logging.error(f"Error checking task status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")