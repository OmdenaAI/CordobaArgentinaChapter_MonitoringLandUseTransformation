from typing import Union, Any
from enum import Enum
from pydantic import BaseModel


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
    