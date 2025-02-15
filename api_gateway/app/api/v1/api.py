from fastapi import APIRouter
from app.api.v1.endpoints import auth, places, processing

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(places.router, prefix="/places", tags=["places"])
api_router.include_router(processing.router, prefix="/processing", tags=["processing"]) 