from typing import Protocol

from app.schemas.location import Location
from app.schemas.weather import WeatherResponse


class WeatherProvider(Protocol):
    """Application-facing provider contract independent of vendor payloads."""

    async def search_locations(self, query: str, *, limit: int = 10) -> list[Location]: ...

    async def get_weather(self, latitude: float, longitude: float) -> WeatherResponse: ...
