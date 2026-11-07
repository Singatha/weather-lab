import pytest

from app.providers.weather_codes import weather_condition


@pytest.mark.parametrize(
    ("code", "category", "description"),
    [
        (0, "clear", "Clear sky"),
        (2, "partly_cloudy", "Partly cloudy"),
        (3, "overcast", "Overcast"),
        (45, "fog", "Fog"),
        (53, "drizzle", "Moderate drizzle"),
        (65, "rain", "Heavy rain"),
        (75, "snow", "Heavy snowfall"),
        (95, "storm", "Thunderstorm"),
        (1000, "unknown", "Unknown weather condition"),
    ],
)
def test_weather_condition_mapping(code: int, category: str, description: str) -> None:
    condition = weather_condition(code)

    assert condition.category == category
    assert condition.description == description
