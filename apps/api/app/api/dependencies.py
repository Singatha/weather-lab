from typing import Annotated, cast

from fastapi import Depends, Request

from app.services.weather import WeatherService


def get_weather_service(request: Request) -> WeatherService:
    return cast(WeatherService, request.app.state.weather_service)


WeatherServiceDependency = Annotated[WeatherService, Depends(get_weather_service)]
