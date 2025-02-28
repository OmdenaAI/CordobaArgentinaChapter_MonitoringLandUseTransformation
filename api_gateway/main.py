from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from celery import Celery
from typing import Dict, List
from celery.result import AsyncResult
from pydantic import BaseModel, Field
from datetime import date
from rate_limit.rate_limiter import RateLimitFactory
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChangeDetectionRequest(BaseModel):
    """
    Pydantic model for change detection request.
    polygon: List of coordinates defining the area of interest
    start_date: Start date for change detection
    end_date: End date for change detection
    period: Time period for analysis (e.g., 'monthly', 'yearly')
    """
    polygon: List[List[float]] = Field(..., description="List of coordinates [[lat, lon], ..]")
    start_date: date = Field(..., description="Start date for change detection")
    end_date: date = Field(..., description="End date for change detection")
    period: str = Field(..., description="Time period for analysis (e.g., 'monthly', 'yearly')")

    class Config:
        json_schema_extra = {
            "example": {
                "polygon": [[-122.5, 37.5], [-122.4, 37.5], [-122.4, 37.6], [-122.5, 37.6], [-122.5, 37.5]],
                "start_date": "2021-01-01",
                "end_date": "2021-12-31",
                "period": "monthly"
            }
        }

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
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

# **New Function - rate_limit_decorator**: A decorator to handle rate-limiting logic
def rate_limit_decorator(func):
    async def wrapper(request: Request):
        client = request.client.host
        try:
            if client not in ip_addresses:
                ip_addresses[client] = RateLimitFactory.get_instance("TokenBucket")
            if ip_addresses[client].allow_request():
                return await func(request)
            else:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
        except RateLimitExceeded as e:
            raise HTTPException(status_code=429, detail=str(e))
    return wrapper

# **Modified - Applying rate_limit_decorator** to the limited endpoint
@app.get("/limited")
@rate_limit_decorator
async def limited(request: Request):
    return "This is a limited use API"

"""
The unlimited endpoint is not rate-limited and can be accessed without any restrictions.
"""
@app.get("/unlimited")
def unlimited(request: Request):
    return "Free to use API limitless"

# Initialize Celery app
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# **Modified - Health check with Celery worker status**:
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

# **Modified - Enhanced logging and task submission handling in process endpoint**:
@app.post("/process")
async def process_change_detection(request: ChangeDetectionRequest) -> Dict[str, str]:
    """
    Submit a change detection request for processing
    Returns a task ID that can be used to check the status of the task.
    """
    try:
        logging.info(f"Processing image")
        # Convert request to dictionary for Celery task
        task_data = request.model_dump()

        # Submit task to Celery
        task = celery_app.send_task("tasks.process_task", args=[task_data])

        logging.info(f"Task submitted with ID: {task.id}")
        return {"task_id": task.id, "status": "submitted"}

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# **Modified - Task status logging and handling**:
@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, str]:
    """
    Get the status of a submitted task by its task ID.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        task_status = task_result.status
        task_result_data = task_result.result if task_result.ready() else None
        logging.info(f"Task {task_id} status: {task_status}")
        return {"task_id": task_id, "status": task_status, "result": task_result_data}

    except Exception as e:
        logging.error(f"Error fetching task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# **Final inclusion of router for versioned API routes**
app.include_router(api_router, prefix=settings.API_V1_STR)
