# API contract — Phase 2

All application endpoints return JSON. Interactive OpenAPI documentation is
available at `/docs`, with the machine-readable schema at `/openapi.json`.

## `GET /health/live`

Confirms that the API process can serve requests.

```json
{"status": "ok"}
```

## `GET /health/ready`

Confirms that application initialization completed. Redis is not an API runtime
dependency until Phase 3.

```json
{"status": "ready"}
```

## `GET /api/v1/locations/search`

Searches Open-Meteo's GeoNames-based location index and returns normalized
locations. Empty searches return an empty `locations` array rather than an
error.

Query parameters:

| Name | Type | Rules |
| --- | --- | --- |
| `q` | string | Required, 2–100 characters, must contain a non-space character |

Example response:

```json
{
  "query": "Berlin",
  "locations": [
    {
      "id": 2950159,
      "name": "Berlin",
      "country": "Germany",
      "country_code": "DE",
      "region": "Berlin",
      "latitude": 52.52437,
      "longitude": 13.41053,
      "timezone": "Europe/Berlin",
      "elevation_m": 74.0,
      "population": 3426354
    }
  ]
}
```

## `GET /api/v1/weather`

Returns current conditions plus hourly and seven-day forecasts in canonical
metric units. Open-Meteo responses are normalized into application schemas.
Timestamps include the searched location's UTC offset.

Query parameters:

| Name | Type | Rules |
| --- | --- | --- |
| `latitude` | number | Required, -90 through 90 |
| `longitude` | number | Required, -180 through 180 |

Top-level response fields:

| Field | Meaning |
| --- | --- |
| `location` | Forecast grid coordinates, elevation, timezone, and offset |
| `current` | Temperature, feels-like, humidity, precipitation, wind, and condition |
| `hourly` | Timezone-aware hourly forecast values |
| `daily` | Seven local forecast dates with high/low, precipitation, sunrise, and sunset |
| `units` | Canonical units: Celsius, km/h, mm, and percent |
| `metadata` | Provider timing, fetch time, and Phase 2 cache status |

`condition` contains the numeric WMO code, an English description, and one of
the UI categories `clear`, `partly_cloudy`, `overcast`, `fog`, `drizzle`,
`rain`, `snow`, `storm`, or `unknown`.

Phase 2 always returns `metadata.cache_status` as `not_cached` and
`metadata.is_stale` as `false`. Phase 3 will extend this metadata when Redis is
integrated.

## Error contract

Expected failures use one envelope:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request parameters are invalid.",
    "details": []
  }
}
```

| Status | Code | Meaning |
| --- | --- | --- |
| `422` | `VALIDATION_ERROR` | Query or coordinate validation failed |
| `502` | `WEATHER_PROVIDER_UNAVAILABLE` | Provider connection or HTTP failure |
| `502` | `INVALID_PROVIDER_RESPONSE` | Provider payload failed validation |
| `503` | `WEATHER_PROVIDER_RATE_LIMITED` | Provider returned a rate limit |
| `504` | `WEATHER_PROVIDER_TIMEOUT` | Configured provider timeout elapsed |
| `500` | `INTERNAL_ERROR` | Unexpected server error |

Retries, circuit breaking, public API rate limiting, and stale fallback belong
to later phases.

