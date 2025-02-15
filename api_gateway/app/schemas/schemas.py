from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, constr, ConfigDict, Field
from datetime import datetime
from enum import Enum

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: constr(min_length=8)

class UserUpdate(UserBase):
    password: Optional[constr(min_length=8)] = None

class UserInDBBase(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str

# Place schemas
class PlaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    geometry: Dict[str, Any] = Field(..., description="GeoJSON format geometry")

    model_config = ConfigDict(from_attributes=True)

class PlaceCreate(PlaceBase):
    pass

class PlaceUpdate(PlaceBase):
    name: Optional[str] = None
    description: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None

class Place(PlaceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        # Si el objeto tiene la propiedad geojson, úsala para la geometría
        if hasattr(obj, 'geojson'):
            obj_dict = {
                'id': obj.id,
                'name': obj.name,
                'description': obj.description,
                'geometry': obj.geojson,
                'user_id': obj.user_id,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at
            }
            return super().model_validate(obj_dict, *args, **kwargs)
        return super().model_validate(obj, *args, **kwargs)

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingBatchBase(BaseModel):
    area_of_interest: Dict[str, Any] = Field(..., description="GeoJSON format geometry")
    start_date: datetime
    end_date: datetime
    place_id: Optional[int] = None

class ProcessingBatchCreate(ProcessingBatchBase):
    pass

class ProcessingBatch(ProcessingBatchBase):
    id: int
    status: ProcessingStatus
    processed_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class DeforestationEventBase(BaseModel):
    affected_area: Dict[str, Any] = Field(..., description="GeoJSON format geometry")
    detected_at: datetime
    confidence_score: float = Field(..., ge=0, le=1)
    area_hectares: float = Field(..., gt=0)

class DeforestationEventCreate(DeforestationEventBase):
    batch_id: int

class DeforestationEvent(DeforestationEventBase):
    id: int
    batch_id: int

    model_config = ConfigDict(from_attributes=True) 