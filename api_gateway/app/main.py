from fastapi import FastAPI, HTTPException, UploadFile, File
from celery import Celery
from typing import Dict, List
from celery.result import AsyncResult
from pydantic import BaseModel, Field
from datetime import date
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

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

# Initialize Celery app
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# Basic health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint to verify the API is running.
    """
    return {"status": "healthy", "service": "land-use-change-api"}

# Receive the request to process and image, submit it to Celery and then return a task ID
@app.post("/process")
async def process_change_detection(request: ChangeDetectionRequest) -> Dict[str, str]:
    """
    Submit a change detection request for processing
    Returns a task ID that can be used to check the status of the task.
    """
    try:
        # Convert request to dictionary for Celery task
        task_data = request.model_dump()

        # Submit task to Celery
        task = celery_app.send_task("tasks.process_task", args=[task_data])

        return {"task_id": task.id, "status": "submitted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

# Get the status of a task by its task ID
@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, str]:
    """
    Get the status of a submitted task by its task ID.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        return {"task_id": task_id, "status": task_result.status, "result": task_result.result if task_result.ready() else None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router, prefix=settings.API_V1_STR)