from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    country: str
    country_code: str = Field(min_length=2, max_length=2)
    region: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str
    elevation_m: float | None = None
    population: int | None = Field(default=None, ge=0)


class LocationSearchResponse(BaseModel):
    query: str
    locations: list[Location]
