from datetime import UTC, date, datetime

from app.schemas.location import Location
from app.schemas.weather import (
    CurrentWeather,
    DailyForecast,
    HourlyForecast,
    WeatherCondition,
    WeatherLocation,
    WeatherMetadata,
    WeatherResponse,
)


def location() -> Location:
    return Location(
        id=2950159,
        name="Berlin",
        country="Germany",
        country_code="DE",
        region="Berlin",
        latitude=52.52437,
        longitude=13.41053,
        timezone="Europe/Berlin",
        elevation_m=74,
        population=3426354,
    )


def weather_response() -> WeatherResponse:
    condition = WeatherCondition(code=0, description="Clear sky", category="clear")
    forecast_time = datetime(2025, 8, 5, 15, tzinfo=UTC)
    return WeatherResponse(
        location=WeatherLocation(
            latitude=52.52,
            longitude=13.41,
            elevation_m=38,
            timezone="Europe/Berlin",
            timezone_abbreviation="CEST",
            utc_offset_seconds=7200,
        ),
        current=CurrentWeather(
            time=forecast_time,
            temperature=20,
            apparent_temperature=18,
            relative_humidity=46,
            precipitation=0,
            wind_speed=14,
            is_day=True,
            condition=condition,
        ),
        hourly=[
            HourlyForecast(
                time=forecast_time,
                temperature=20,
                relative_humidity=46,
                precipitation=0,
                precipitation_probability=5,
                wind_speed=14,
                is_day=True,
                condition=condition,
            )
        ],
        daily=[
            DailyForecast(
                date=date(2025, 8, 5),
                temperature_max=24,
                temperature_min=14,
                precipitation_sum=0,
                precipitation_probability_max=5,
                sunrise=datetime(2025, 8, 5, 5, 31, tzinfo=UTC),
                sunset=datetime(2025, 8, 5, 20, 52, tzinfo=UTC),
                condition=condition,
            )
        ],
        metadata=WeatherMetadata(
            fetched_at=datetime(2025, 8, 5, 13, tzinfo=UTC),
            provider_generation_time_ms=0.12,
        ),
    )
