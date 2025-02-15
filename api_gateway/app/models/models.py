from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from app.db.session import Base
from passlib.hash import bcrypt

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    places = relationship("Place", back_populates="user")
    processing_batches = relationship("ProcessingBatch", back_populates="user")

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return bcrypt.hash(password)

class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    geometry = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="places")
    processing_batches = relationship("ProcessingBatch", back_populates="place")

    @property
    def geojson(self):
        """Convert the geometry to GeoJSON format"""
        if self.geometry is not None:
            shape = to_shape(self.geometry)
            return shape.__geo_interface__
        return None

class ProcessingBatch(Base):
    __tablename__ = "processing_batches"

    id = Column(Integer, primary_key=True, index=True)
    area_of_interest = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="pending")  # Values: pending, processing, completed, failed
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id"))
    
    # Relationships
    user = relationship("User", back_populates="processing_batches")
    place = relationship("Place", back_populates="processing_batches")
    deforestation_events = relationship("DeforestationEvent", back_populates="batch")

    @property
    def geojson(self):
        if self.area_of_interest is not None:
            shape = to_shape(self.area_of_interest)
            return shape.__geo_interface__
        return None

class DeforestationEvent(Base):
    __tablename__ = "deforestation_events"

    id = Column(Integer, primary_key=True, index=True)
    affected_area = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    confidence_score = Column(Float, nullable=False)
    area_hectares = Column(Float, nullable=False)
    batch_id = Column(Integer, ForeignKey("processing_batches.id"), nullable=False)
    
    # Relationships
    batch = relationship("ProcessingBatch", back_populates="deforestation_events")

    @property
    def geojson(self):
        if self.affected_area is not None:
            shape = to_shape(self.affected_area)
            return shape.__geo_interface__
        return None 