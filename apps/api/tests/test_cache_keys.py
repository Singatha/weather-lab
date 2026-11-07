from app.cache.keys import location_search_cache_key, weather_cache_key


def test_location_key_is_case_and_whitespace_insensitive() -> None:
    assert location_search_cache_key("  New   York ") == location_search_cache_key("new york")


def test_location_key_does_not_expose_user_input() -> None:
    key = location_search_cache_key("Berlin")

    assert "Berlin" not in key
    assert key.startswith("weather-lab:v1:locations:")


def test_weather_key_is_stable_at_six_decimal_places() -> None:
    assert weather_cache_key(52.5200001, 13.4099999) == weather_cache_key(52.52, 13.41)
    assert weather_cache_key(52.52, 13.41).endswith("52.520000:13.410000")
