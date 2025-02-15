from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from app.models.models import ProcessingBatch, DeforestationEvent
from app.schemas.schemas import ProcessingBatchCreate, DeforestationEventCreate

# Constants for status
PENDING = "pending"
PROCESSING = "processing"
COMPLETED = "completed"
FAILED = "failed"

def create_processing_batch(
    db: Session,
    *,
    batch_in: ProcessingBatchCreate,
    user_id: int
) -> ProcessingBatch:
    """Create a new processing batch"""
    geometry = from_shape(shape(batch_in.area_of_interest), srid=4326)
    db_batch = ProcessingBatch(
        area_of_interest=geometry,
        start_date=batch_in.start_date,
        end_date=batch_in.end_date,
        place_id=batch_in.place_id,
        user_id=user_id,
        status=PENDING
    )
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

def get_processing_batch(db: Session, batch_id: int) -> Optional[ProcessingBatch]:
    """Get a processing batch by ID"""
    return db.query(ProcessingBatch).filter(ProcessingBatch.id == batch_id).first()

def get_user_processing_batches(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ProcessingBatch]:
    """Get all processing batches for a user"""
    return db.query(ProcessingBatch)\
        .filter(ProcessingBatch.user_id == user_id)\
        .offset(skip)\
        .limit(limit)\
        .all()

def update_batch_status(
    db: Session,
    *,
    batch_id: int,
    status: str,
    error_message: Optional[str] = None
) -> ProcessingBatch:
    """Update the status of a processing batch"""
    batch = get_processing_batch(db, batch_id)
    if not batch:
        return None
    
    batch.status = status
    if status == COMPLETED:
        batch.completed_at = datetime.utcnow()
    if error_message:
        batch.error_message = error_message
    
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch

def create_deforestation_event(
    db: Session,
    *,
    event_in: DeforestationEventCreate
) -> DeforestationEvent:
    """Create a new deforestation event"""
    geometry = from_shape(shape(event_in.affected_area), srid=4326)
    db_event = DeforestationEvent(
        affected_area=geometry,
        detected_at=event_in.detected_at,
        confidence_score=event_in.confidence_score,
        area_hectares=event_in.area_hectares,
        batch_id=event_in.batch_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_batch_events(
    db: Session,
    batch_id: int,
    min_confidence: float = 0.0
) -> List[DeforestationEvent]:
    """Get all deforestation events for a batch"""
    return db.query(DeforestationEvent)\
        .filter(
            DeforestationEvent.batch_id == batch_id,
            DeforestationEvent.confidence_score >= min_confidence
        )\
        .all()

def check_area_processed(
    db: Session,
    *,
    geometry: dict,
    start_date: datetime,
    end_date: datetime
) -> bool:
    """Check if an area has been processed for a given time period"""
    area = from_shape(shape(geometry), srid=4326)
    existing_batch = db.query(ProcessingBatch)\
        .filter(
            func.ST_Intersects(ProcessingBatch.area_of_interest, area),
            ProcessingBatch.start_date == start_date,
            ProcessingBatch.end_date == end_date,
            ProcessingBatch.status == COMPLETED
        )\
        .first()
    return existing_batch is not None

def get_total_deforestation_area(
    db: Session,
    batch_id: int,
    min_confidence: float = 0.7
) -> float:
    """Get total deforested area for a batch"""
    result = db.query(func.sum(DeforestationEvent.area_hectares))\
        .filter(
            DeforestationEvent.batch_id == batch_id,
            DeforestationEvent.confidence_score >= min_confidence
        )\
        .scalar()
    return result or 0.0 