from typing import Union, Any, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import date


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    
    class Config:
        json_schema_extra  = {
            "example": {
                "status": "healthy", 
                "service": "land-use-change-api"
            }
        }


class NumberToSquare(BaseModel):
    number: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "number": 3
            }
        }

class TaskIDSchema(BaseModel):
    task_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "4e992e32-d930-489f-9bd5-a3fe797c0966"
            }
        }
        

class TaskStatusEnum(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatusEnum  # Use Enum here

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "4e992e32-d930-489f-9bd5-a3fe797c0966",
                "status": "SUCCESS"
            }
        }

        

class TaskSuccessResponse(BaseModel):
    task_id: str
    result: Any

    class Config:      
        json_schema_extra = {
            "example": {
                "task_id": "4e992e32-d930-489f-9bd5-a3fe797c0966",
                "result": 9
            }
        }


class TaskPendingOrFailedResponse(BaseModel):
    task_id: str
    message: str

    class Config:       
        json_schema_extra = {
            "example": {
                "task_id": "4e992e32-d930-489f-9bd5-a3fe797c0966",
                "message": "Task not completed yet"
            }
        }


# Response type that can be either success or pending/failed
TaskResultResponse = Union[TaskSuccessResponse, TaskPendingOrFailedResponse]
    
    
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