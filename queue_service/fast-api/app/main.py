import logging
from fastapi import FastAPI, HTTPException, UploadFile, BackgroundTasks
from celery.result import AsyncResult


from celery_config import celery_app
from schemas import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Land Use Change Detection API",
    description="API for Land Use Change Detection",
    version="0.1.0"
)
        
@app.post("/test")
async def test_endpoint(data: NumberToSquare) -> TaskIDSchema:
    try:
        # Use send_task to call the Celery task dynamically
        task = celery_app.send_task("tasks.square_number", args=[data.number])

        # Return the task ID to the client
        return TaskIDSchema(task_id=task.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 


@app.get("/status/{task_id}")
def check_status(task_id: str) -> TaskStatusResponse:
    """
    Checks the current status of a Celery task by ID.
    """
    try:
        task_result: AsyncResult = AsyncResult(task_id, app=celery_app)
        return TaskStatusResponse(task_id=task_id, status=task_result.status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 


@app.get("/results/{task_id}")
def get_results(task_id: str) -> TaskResultResponse:
    """
    Returns the final results or any output data from the completed task.
    """
    try:
        task_result: AsyncResult = AsyncResult(task_id, app=celery_app)
        if task_result.ready():
            return TaskSuccessResponse(task_id=task_id, result=task_result.result)
        else:
            return TaskPendingOrFailedResponse(task_id=task_id, message="Task not completed yet")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
