from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.services import place_service
from app.schemas.schemas import Place, PlaceCreate, PlaceUpdate, User

router = APIRouter()

def serialize_place(place):
    """Helper function to serialize a place object to a dictionary"""
    return {
        "id": place.id,
        "name": place.name,
        "description": place.description,
        "geometry": place.geojson,
        "user_id": place.user_id,
        "created_at": place.created_at,
        "updated_at": place.updated_at
    }

@router.post("/", response_model=Place)
def create_place(
    *,
    db: Session = Depends(deps.get_db),
    place_in: PlaceCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Crear un nuevo lugar.
    """
    place = place_service.create_place(db=db, place_in=place_in, user_id=current_user.id)
    return serialize_place(place)

@router.get("/", response_model=List[Place])
def get_places(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener lugares del usuario actual.
    """
    places = place_service.get_places_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return [serialize_place(place) for place in places]

@router.get("/{place_id}", response_model=Place)
def get_place(
    *,
    db: Session = Depends(deps.get_db),
    place_id: int,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener un lugar por ID.
    """
    place = place_service.get_place(db=db, place_id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    if place.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return serialize_place(place)

@router.put("/{place_id}", response_model=Place)
def update_place(
    *,
    db: Session = Depends(deps.get_db),
    place_id: int,
    place_in: PlaceUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Actualizar un lugar.
    """
    place = place_service.get_place(db=db, place_id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    if place.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    place = place_service.update_place(db=db, db_obj=place, obj_in=place_in)
    return serialize_place(place)

@router.delete("/{place_id}", response_model=Place)
def delete_place(
    *,
    db: Session = Depends(deps.get_db),
    place_id: int,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Eliminar un lugar.
    """
    place = place_service.get_place(db=db, place_id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    if place.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    place = place_service.delete_place(db=db, place_id=place_id)
    return serialize_place(place)

@router.get("/bbox/", response_model=List[Place])
def get_places_in_bbox(
    *,
    db: Session = Depends(deps.get_db),
    min_lon: float = Query(..., description="Longitud mínima del bounding box"),
    min_lat: float = Query(..., description="Latitud mínima del bounding box"),
    max_lon: float = Query(..., description="Longitud máxima del bounding box"),
    max_lat: float = Query(..., description="Latitud máxima del bounding box"),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener lugares dentro de un bounding box.
    """
    places = place_service.get_places_in_bbox(
        db=db,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat
    )
    return [serialize_place(place) for place in places]

@router.get("/nearby/", response_model=List[Place])
def get_places_within_distance(
    *,
    db: Session = Depends(deps.get_db),
    lat: float = Query(..., description="Latitud del punto central"),
    lon: float = Query(..., description="Longitud del punto central"),
    distance: float = Query(..., description="Distancia en metros"),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener lugares dentro de una distancia específica de un punto.
    """
    places = place_service.get_places_within_distance(
        db=db,
        lat=lat,
        lon=lon,
        distance_meters=distance
    )
    return [serialize_place(place) for place in places] 