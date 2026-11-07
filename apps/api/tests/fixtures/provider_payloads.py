from typing import Any


def geocoding_payload() -> dict[str, Any]:
    return {
        "results": [
            {
                "id": 2950159,
                "name": "Berlin",
                "latitude": 52.52437,
                "longitude": 13.41053,
                "elevation": 74.0,
                "country_code": "DE",
                "timezone": "Europe/Berlin",
                "population": 3426354,
                "country": "Germany",
                "admin1": "Berlin",
            }
        ]
    }


def forecast_payload() -> dict[str, Any]:
    return {
        "latitude": 52.52,
        "longitude": 13.419,
        "generationtime_ms": 0.123,
        "utc_offset_seconds": 7200,
        "timezone": "Europe/Berlin",
        "timezone_abbreviation": "CEST",
        "elevation": 38.0,
        "current": {
            "time": "2025-08-05T15:00",
            "temperature_2m": 20.2,
            "relative_humidity_2m": 46,
            "apparent_temperature": 18.4,
            "is_day": 1,
            "precipitation": 0.0,
            "weather_code": 0,
            "wind_speed_10m": 14.2,
        },
        "hourly": {
            "time": ["2025-08-05T15:00", "2025-08-05T16:00"],
            "temperature_2m": [20.2, 19.8],
            "relative_humidity_2m": [46, 49],
            "precipitation": [0.0, 0.2],
            "precipitation_probability": [5, 20],
            "weather_code": [0, 2],
            "wind_speed_10m": [14.2, 13.8],
            "is_day": [1, 1],
        },
        "daily": {
            "time": ["2025-08-05", "2025-08-06"],
            "temperature_2m_max": [24.1, 21.3],
            "temperature_2m_min": [14.2, 15.1],
            "precipitation_sum": [0.2, 2.4],
            "precipitation_probability_max": [20, 65],
            "weather_code": [2, 61],
            "sunrise": ["2025-08-05T05:31", "2025-08-06T05:33"],
            "sunset": ["2025-08-05T20:52", "2025-08-06T20:50"],
        },
    }
