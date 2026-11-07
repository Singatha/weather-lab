from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

WeatherCategory = Literal[
    "clear",
    "partly_cloudy",
    "overcast",
    "fog",
    "drizzle",
    "rain",
    "snow",
    "storm",
    "unknown",
]


class WeatherCondition(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: int
    description: str
    category: WeatherCategory


class CurrentWeather(BaseModel):
    time: datetime
    temperature: float
    apparent_temperature: float
    relative_humidity: int = Field(ge=0, le=100)
    precipitation: float = Field(ge=0)
    wind_speed: float = Field(ge=0)
    is_day: bool
    condition: WeatherCondition


class HourlyForecast(BaseModel):
    time: datetime
    temperature: float
    relative_humidity: int = Field(ge=0, le=100)
    precipitation: float = Field(ge=0)
    precipitation_probability: int = Field(ge=0, le=100)
    wind_speed: float = Field(ge=0)
    is_day: bool
    condition: WeatherCondition


class DailyForecast(BaseModel):
    date: date
    temperature_max: float
    temperature_min: float
    precipitation_sum: float = Field(ge=0)
    precipitation_probability_max: int = Field(ge=0, le=100)
    sunrise: datetime
    sunset: datetime
    condition: WeatherCondition


class WeatherUnits(BaseModel):
    temperature: Literal["celsius"] = "celsius"
    wind_speed: Literal["km/h"] = "km/h"
    precipitation: Literal["mm"] = "mm"
    relative_humidity: Literal["percent"] = "percent"


class WeatherLocation(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    elevation_m: float | None = None
    timezone: str
    timezone_abbreviation: str
    utc_offset_seconds: int


class WeatherMetadata(BaseModel):
    provider: Literal["open-meteo"] = "open-meteo"
    fetched_at: datetime
    provider_generation_time_ms: float = Field(ge=0)
    cache_status: Literal["not_cached"] = "not_cached"
    is_stale: Literal[False] = False


class WeatherResponse(BaseModel):
    location: WeatherLocation
    current: CurrentWeather
    hourly: list[HourlyForecast]
    daily: list[DailyForecast]
    units: WeatherUnits = Field(default_factory=WeatherUnits)
    metadata: WeatherMetadata
