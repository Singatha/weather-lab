from app.providers.base import WeatherProvider
from app.schemas.location import LocationSearchResponse
from app.schemas.weather import WeatherResponse


class WeatherService:
    """Coordinate weather use cases without exposing provider details."""

    def __init__(self, provider: WeatherProvider) -> None:
        self._provider = provider

    async def search_locations(self, query: str) -> LocationSearchResponse:
        normalized_query = query.strip()
        locations = await self._provider.search_locations(normalized_query)
        return LocationSearchResponse(query=normalized_query, locations=locations)

    async def get_weather(self, latitude: float, longitude: float) -> WeatherResponse:
        return await self._provider.get_weather(latitude, longitude)
