"""Draft that integrates services defined in api_gateway/app"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from api_gateway.app.services.place_service import get_places_in_bbox
from api_gateway.app.services.processing_service import get_user_processing_batches
from api_gateway.app.db.session import get_db
from sandbox.RSaini.tasks_working import process_deforestation

app = FastAPI()

@app.get("/places/")
def list_places_in_bbox(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float, db: Session = Depends(get_db)
):
    """Retrieve places within a bounding box"""
    return get_places_in_bbox(db, min_lon, min_lat, max_lon, max_lat)

@app.get("/processing/")
def list_processing_batches(user_id: int, db: Session = Depends(get_db)):
    """Retrieve processing batches for a user"""
    return get_user_processing_batches(db, user_id)

@app.post("/process/")
def start_deforestation_processing(batch_data: dict, user_id: int):
    """Trigger a Celery task for deforestation detection"""
    task = process_deforestation.apply_async(args=[batch_data, user_id])
    return {"task_id": task.id, "status": "queued"}
