"""Draft that integrates services defined in api_gateway/app"""
from celery import Celery
from sqlalchemy.orm import Session
from api_gateway.app.services.processing_service import (
    create_processing_batch,
    update_batch_status,
    create_deforestation_event
)
from api_gateway.app.db.session import get_db

celery = Celery("tasks", broker="redis://localhost:6379/0")


@celery.task
def process_deforestation(batch_data: dict, user_id: int):
    """Celery task to process a deforestation detection batch."""
    db: Session = next(get_db())

    # Create a new processing batch
    batch = create_processing_batch(db, batch_in=batch_data, user_id=user_id)

    if not batch:
        return {"error": "Failed to create batch"}

    update_batch_status(db, batch_id=batch.id, status="processing")

    try:
        # Simulate processing (replace with actual ML model execution)
        deforestation_events = run_deforestation_model(batch_data["area_of_interest"])

        # Save events
        for event in deforestation_events:
            create_deforestation_event(db, event_in=event)

        update_batch_status(db, batch_id=batch.id, status="completed")
        return {"batch_id": batch.id, "status": "completed"}

    except Exception as e:
        update_batch_status(db, batch_id=batch.id, status="failed", error_message=str(e))
        return {"error": str(e)}

