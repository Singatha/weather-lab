from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import WeatherServiceDependency
from app.schemas.errors import ErrorEnvelope
from app.schemas.weather import WeatherResponse

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get(
    "",
    response_model=WeatherResponse,
    responses={
        422: {"model": ErrorEnvelope},
        502: {"model": ErrorEnvelope},
        503: {"model": ErrorEnvelope},
        504: {"model": ErrorEnvelope},
    },
    summary="Get a seven-day weather forecast",
)
async def get_weather(
    service: WeatherServiceDependency,
    latitude: Annotated[float, Query(ge=-90, le=90, examples=[52.52])],
    longitude: Annotated[float, Query(ge=-180, le=180, examples=[13.41])],
) -> WeatherResponse:
    return await service.get_weather(latitude, longitude)
