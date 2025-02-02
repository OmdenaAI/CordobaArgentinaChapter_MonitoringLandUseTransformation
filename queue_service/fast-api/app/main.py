import logging
from fastapi import FastAPI, UploadFile, BackgroundTasks
from typing import Dict, Any
from celery.result import AsyncResult


from celery_config import celery_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app: FastAPI = FastAPI()


@app.post("/test")
async def test_endpoint(data: int) -> Dict[str, str]:
    # Use send_task to call the Celery task dynamically
    task = celery_app.send_task("tasks.square_number", args=[data.number])

    # Return the task ID to the client
    return {"task_id": task.id}


@app.get("/status/{task_id}")
def check_status(task_id: str) -> Dict[str, str]:
    """
    Checks the current status of a Celery task by ID.
    """
    task_result: AsyncResult = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": task_result.status}


@app.get("/results/{task_id}")
def get_results(task_id: str) -> Dict[str, Any]:
    """
    Returns the final results or any output data from the completed task.
    """
    task_result: AsyncResult = AsyncResult(task_id, app=celery_app)
    if task_result.ready():
        return {"task_id": task_id, "result": task_result.result}
    else:
        return {"task_id": task_id, "message": "Task not completed yet"}
