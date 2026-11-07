from hashlib import sha256

_CACHE_SCHEMA_VERSION = "v1"


def location_search_cache_key(query: str) -> str:
    normalized = " ".join(query.casefold().split())
    digest = sha256(normalized.encode("utf-8")).hexdigest()
    return f"weather-lab:{_CACHE_SCHEMA_VERSION}:locations:{digest}"


def weather_cache_key(latitude: float, longitude: float) -> str:
    return f"weather-lab:{_CACHE_SCHEMA_VERSION}:weather:metric:{latitude:.6f}:{longitude:.6f}"
