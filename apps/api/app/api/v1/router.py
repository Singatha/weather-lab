from fastapi import APIRouter

from app.api.v1.locations import router as locations_router
from app.api.v1.weather import router as weather_router

router = APIRouter(prefix="/api/v1")
router.include_router(locations_router)
router.include_router(weather_router)
