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

# Import Celery task to trigger preprocessing and prediction
from CordobaArgentinaChapter_MonitoringLandUseTransformation.queue_system.tasks import run_preprocessing_and_prediction

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

# **New Task to be triggered with Celery**: process_change_detection
@app.post("/process")
@rate_limit_decorator
async def process_change_detection(request: ChangeDetectionRequest) -> Dict[str, str]:
    """
    Submit a change detection request for processing
    Returns a task ID that can be used to check the status of the task.
    """
    try:
        logging.info(f"Processing change detection request")

        # Convert request to dictionary for Celery task
        task_data = request.dict()

        # Extract the necessary details for roi and days
        roi = task_data.get("polygon")
        days = [task_data.get("start_date"), task_data.get("end_date")]

        # Log the extracted inputs
        logging.info(f"ROI: {roi}, Start Date: {days[0]}, End Date: {days[1]}")

        # Submit task to Celery
        task = run_preprocessing_and_prediction.apply_async(args=[roi, days])

        logging.info(f"Task submitted with ID: {task.id}")
        return {"task_id": task.id, "status": "submitted"}

    except Exception as e:
        logging.error(f"Error processing change detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# **Modified Task Status Endpoint** to include the result:
@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, str]:
    """
    Get the status of a submitted task by its task ID and return the result.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        task_status = task_result.status
        task_result_data = task_result.result if task_result.ready() else None

        if task_result.ready():
            # If the task is done, return the deforest_rois result
            logging.info(f"Task {task_id} completed successfully")
            return {"task_id": task_id, "status": task_status, "result": task_result_data}

        logging.info(f"Task {task_id} is still processing")
        return {"task_id": task_id, "status": task_status}

    except Exception as e:
        logging.error(f"Error fetching task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check to verify the system's status
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

# Include versioned API routes
app.include_router(api_router, prefix=settings.API_V1_STR)