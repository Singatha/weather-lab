from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import WeatherServiceDependency
from app.schemas.errors import ErrorEnvelope
from app.schemas.location import LocationSearchResponse

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get(
    "/search",
    response_model=LocationSearchResponse,
    responses={422: {"model": ErrorEnvelope}, 502: {"model": ErrorEnvelope}},
    summary="Search for locations",
)
async def search_locations(
    service: WeatherServiceDependency,
    q: Annotated[
        str,
        Query(
            min_length=2,
            max_length=100,
            pattern=r".*\S.*",
            description="Location name or postal code",
            examples=["Berlin"],
        ),
    ],
) -> LocationSearchResponse:
    return await service.search_locations(q)
