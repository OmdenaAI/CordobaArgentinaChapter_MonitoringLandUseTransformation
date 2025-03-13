from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from celery import Celery
from typing import Dict, List
from celery.result import AsyncResult


from pydantic import BaseModel, Field
from datetime import date
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

import logging

# Import the tasks from the queue system  
# Needs to be adjusted based on the actual implementation
from queue_service.tasks import *

# Rate limiter for the API
# Needs to be adjusted based on the actual implementation
from rate_limit.rate_limiter import RateLimitFactory
from rate_limit.limiting_algorithms import RateLimitExceeded

# Import the CordobaDataPreprocessor class
# Needs to be adjusted based on the actual implementation
# Changed the paths classes
from demo_processing_prediction.cordobaDataPreprocessor import *
from demo_processing_prediction.cordobaPredictor import *

#########################################################
# Import database connection helpers and models
# Needs to be adjusted based on the actual implementation of the database
from models import RequestData, Result
from database import get_db
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChangeDetectionRequest(BaseModel):
    """
    Pydantic model for change detection request.

    Constructor for an instance of CordobaImage.
    gee_account: Login info to GEE
    gee_credentials_path: Login info to GEE
    days: the dates T1 and T2 e.g., ["2021-01-01", "2022-12-31"]
    roi_coords: the bounding longitudes and latitudes of the image, below it is represented by the roi_coords
    """
    gee_account: str = Field(..., description="Google Earth Engine account ID")
    gee_credentials_path: str = Field(..., description="../../../earthengine_api_key.json")
    days: List[str] = Field(..., description='The dates T1 and T2 as selected by the user (eg. days = ["2021-01-01", "2022-12-31"])')
    roi_coords: List[List[float]]  = Field(..., description="The area selected by the user.")
   
    class Config:
        json_schema_extra = {
            "example": {
                "gee_account": "cordoba-team",
                "gee_credentials_path": "/path/to/credentials.json",
                "days": ["2021-01-01", "2022-12-31"],
                "area of interest": [[[-63.42803671537233, -30.42050193711671],
                                    [-63.42803671537233, -30.339391209687783],
                                    [-63.34916140311282, -30.339391209687783],
                                    [-63.34916140311282, -30.339391209687783]]]
                },
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

# Endpoint to preprocess the data and fetch images, start the Celery chain
@app.post("/process_request/")
async def process_request(request_data: ChangeDetectionRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Endpoint to preprocess the request and fetch satellite images asynchronously.
    The task is added to the background queue and runs independently.
    It first checks if there is an existing record in the database with the same request already processed.
    If there is a record, it returns the already recorded result.
    If there is no record, it trigger the task chain
    Returns a message indicating the preprocessing has started and the task_id.
    """
    try:
        # Logging for debugging purposes
        logging.info(f"Received request to process image for dates: {request_data.days} and ROI coordinates: {request_data.roi_coords}")
        
        #############################
        # Needs to be adjusted based on the implementation of the database
        # Generate a hash from the request_data (could be a specific identifier like a UUID)
        request_hash = str(request_data.days, request_data.roi_coords)

        # Check if this request was already processed and saved in the database
        existing_result = db.query(Result).filter(Result.request_hash == request_hash).first()

        if existing_result:
            # If the result exists, return it without processing again
            return {"status": "success", "result": existing_result.result}

        # If not already processed, trigger the task chain
        # Start with the preprocessing task, which will return the images
        task = preprocess_images.apply_async(request_data.gee_account, request_data.gee_credentials_path, request_data.days, request_data.roi_coords)

        # After preprocessing, trigger deforestation prediction and save the result
        # Correctly execute the chain by passing the images from preprocess_images to predict_and_save
        task_chain = task.then(predict_deforestation.s(db, request_data.days, request_data.roi_coords))  # Chain the tasks

        # Execute the task chain (this is where the tasks will actually run)
        task_chain_result = task_chain.apply_async()  # Execute the chain
 
        #############################
        # Needs to be adjusted based on the database implementation
        # Store the request in the database as pending
        db.add(RequestData(request_hash=request_hash, status="pending"))
        db.commit()

        # Logging for debugging purposes
        logging.info(f"Task submitted with ID: {task_chain_result.id}")

        # Return a success message indicating the task has been initiated
        return {"message": "Image preprocessing and deforestation prediction started in the background.", "task_id": task_chain_result.id}

    except Exception as e:
        # Logging for debugging purposes
        logging.error(f"Error during task execution: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

# Endpoint to get the task status
@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, str]:
    """
    The endpoint can be used to check the current status of the tasks in Celery
    There are three options for status:  (PENDING, SUCCESS, or FAILURE).
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.state == 'PENDING':
            return {"task_id": task_id, "status": "pending"}
        elif task_result.state == 'SUCCESS':
            return {"task_id": task_id, "status": "completed", "result": task_result.result}
        elif task_result.state == 'FAILURE':
            return {"task_id": task_id, "status": "failed", "error": str(task_result.info)}
        else:
            return {"task_id": task_id, "status": task_result.state}

    except Exception as e:
        logging.error(f"Error checking task status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")