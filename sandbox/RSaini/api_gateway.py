from fastapi import FastAPI
from pydantic import BaseModel
from sandbox.RSaini.tasks import run_get_satellite_data
from celery.result import AsyncResult

app = FastAPI()

# Pydantic model to parse request data
class ImageRequest(BaseModel):
    date: str  # Date for the image
    area: dict  # Bounding box for the area of interest
    source: str  # Data source (e.g., 'SENTINEL2')

@app.post("/run_get_satellite_data")
async def run_get_satellite_data_endpoint(request: ImageRequest):
    """
    Endpoint to trigger the Celery task to run get_satellite_data.

    Args:
        request: JSON body containing:
            - date: str
            - area: dict
            - source: str

    Returns:
        JSON response with task ID.
    """
    task = run_get_satellite_data.apply_async(args=[request.dict()])
    return {"task_id": task.id, "status": "Task is running"}

@app.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    """
    Endpoint to check the status of the task.

    Args:
        task_id: ID of the Celery task.

    Returns:
        JSON response with task status.
    """
    task_result = AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": task_result.state,
        "result": task_result.result if task_result.ready() else None
    }