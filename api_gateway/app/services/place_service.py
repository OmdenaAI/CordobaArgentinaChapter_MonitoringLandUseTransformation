from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape
from app.models.models import Place, User
from app.schemas.schemas import PlaceCreate, PlaceUpdate

def create_place(db: Session, *, place_in: PlaceCreate, user_id: int) -> Place:
    """Crear un nuevo lugar"""
    # Convert GeoJSON to WKB format for storage
    geometry = from_shape(shape(place_in.geometry), srid=4326)
    db_place = Place(
        name=place_in.name,
        description=place_in.description,
        geometry=geometry,
        user_id=user_id
    )
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    
    # Convert geometry to GeoJSON before returning
    return db_place

def get_place(db: Session, place_id: int) -> Optional[Place]:
    """Obtener un lugar por su ID"""
    place = db.query(Place).filter(Place.id == place_id).first()
    return place

def get_places_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Place]:
    """Obtener todos los lugares de un usuario"""
    places = db.query(Place).filter(Place.user_id == user_id).offset(skip).limit(limit).all()
    return places

def update_place(db: Session, *, db_obj: Place, obj_in: PlaceUpdate) -> Place:
    """Actualizar un lugar"""
    update_data = obj_in.model_dump(exclude_unset=True)
    if 'geometry' in update_data:
        update_data['geometry'] = from_shape(shape(update_data['geometry']), srid=4326)
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_place(db: Session, *, place_id: int) -> Place:
    """Eliminar un lugar"""
    place = db.query(Place).filter(Place.id == place_id).first()
    db.delete(place)
    db.commit()
    return place

def get_places_in_bbox(
    db: Session,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float
) -> List[Place]:
    """Obtener lugares dentro de un bounding box"""
    bbox = f'SRID=4326;POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))'
    places = db.query(Place).filter(func.ST_Intersects(Place.geometry, bbox)).all()
    return places

def get_places_within_distance(
    db: Session,
    lat: float,
    lon: float,
    distance_meters: float
) -> List[Place]:
    """Obtener lugares dentro de una distancia específica de un punto"""
    point = f'SRID=4326;POINT({lon} {lat})'
    places = db.query(Place).filter(
        func.ST_DWithin(
            func.ST_Transform(Place.geometry, 3857),
            func.ST_Transform(func.ST_GeomFromEWKT(point), 3857),
            distance_meters
        )
    ).all()
    return places 