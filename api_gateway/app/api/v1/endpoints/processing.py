from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.services import processing_service
from app.schemas.schemas import (
    ProcessingBatch,
    ProcessingBatchCreate,
    DeforestationEvent,
    User
)

router = APIRouter()

@router.post("/batch/", response_model=ProcessingBatch)
def create_batch(
    *,
    db: Session = Depends(deps.get_db),
    batch_in: ProcessingBatchCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Create a new processing batch.
    """
    # Check if area has been processed
    if processing_service.check_area_processed(
        db=db,
        geometry=batch_in.area_of_interest,
        start_date=batch_in.start_date,
        end_date=batch_in.end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="This area has already been processed for the specified time period"
        )
    
    return processing_service.create_processing_batch(
        db=db,
        batch_in=batch_in,
        user_id=current_user.id
    )

@router.get("/batch/", response_model=List[ProcessingBatch])
def get_batches(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get all processing batches for current user.
    """
    return processing_service.get_user_processing_batches(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

@router.get("/batch/{batch_id}", response_model=ProcessingBatch)
def get_batch(
    *,
    db: Session = Depends(deps.get_db),
    batch_id: int,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get a specific processing batch.
    """
    batch = processing_service.get_processing_batch(db=db, batch_id=batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return batch

@router.get("/batch/{batch_id}/events", response_model=List[DeforestationEvent])
def get_batch_events(
    *,
    db: Session = Depends(deps.get_db),
    batch_id: int,
    min_confidence: float = Query(0.0, ge=0, le=1),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get all deforestation events for a batch.
    """
    batch = processing_service.get_processing_batch(db=db, batch_id=batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return processing_service.get_batch_events(
        db=db,
        batch_id=batch_id,
        min_confidence=min_confidence
    )

@router.get("/batch/{batch_id}/total-area")
def get_total_deforestation(
    *,
    db: Session = Depends(deps.get_db),
    batch_id: int,
    min_confidence: float = Query(0.7, ge=0, le=1),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get total deforested area for a batch.
    """
    batch = processing_service.get_processing_batch(db=db, batch_id=batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    total_area = processing_service.get_total_deforestation_area(
        db=db,
        batch_id=batch_id,
        min_confidence=min_confidence
    )
    
    return {
        "batch_id": batch_id,
        "total_area_hectares": total_area,
        "min_confidence": min_confidence
    } 