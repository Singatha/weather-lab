# API contract — Phase 6

All application endpoints return JSON. Interactive OpenAPI documentation is
available at `/docs`, with the machine-readable schema at `/openapi.json`.

Every response includes `X-Request-ID`. A valid caller-supplied ID is echoed;
otherwise the API generates a UUID. Clients should include this value in support
or incident reports.

## `GET /health/live`

Confirms that the API process can serve requests.

```json
{"status": "ok"}
```

## `GET /health/ready`

Confirms that application initialization completed. Redis is degradable, so an
unavailable cache is reported without making the endpoint fail.

```json
{"status": "ready", "dependencies": {"redis": "ok"}}
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
| `metadata` | Provider timing, fetch time, cache state, and stale state |

`condition` contains the numeric WMO code, an English description, and one of
the UI categories `clear`, `partly_cloudy`, `overcast`, `fog`, `drizzle`,
`rain`, `snow`, `storm`, or `unknown`.

`metadata.cache_status` has these values:

| Value | Meaning |
| --- | --- |
| `miss` | Open-Meteo was called and the response was cached |
| `hit` | A fresh Redis value was returned |
| `stale` | Open-Meteo failed and a retained stale value was returned |
| `bypass` | Redis failed, so fresh provider data was returned without caching |

`metadata.is_stale` is true only for stale fallback. `cached_at` records when a
successfully cached weather response was written.

## Rate limiting

`/api/v1/*` responses include:

| Header | Meaning |
| --- | --- |
| `X-RateLimit-Limit` | Configured request quota |
| `X-RateLimit-Remaining` | Requests left in the current fixed window |
| `X-RateLimit-Reset` | Seconds until the current window resets |

Exceeded quotas return `429`, set `Retry-After`, and use the standard error
envelope. Health and documentation endpoints are not rate limited. Client
identity uses the direct socket address; trusted-proxy forwarding configuration
belongs to the deployment phase.

## `GET /metrics`

Returns the Prometheus text exposition for HTTP latency and errors, cache
operations, and provider outcomes/latency. This operational endpoint is not
included in OpenAPI and is not rate limited. Deployment controls for restricting
scrape access belong to Phase 7.

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
| `429` | `RATE_LIMIT_EXCEEDED` | Client quota was exhausted |
| `502` | `WEATHER_PROVIDER_UNAVAILABLE` | Provider connection or HTTP failure |
| `502` | `WEATHER_PROVIDER_REQUEST_REJECTED` | Provider rejected a non-retryable request |
| `502` | `INVALID_PROVIDER_RESPONSE` | Provider payload failed validation |
| `503` | `WEATHER_PROVIDER_RATE_LIMITED` | Provider returned a rate limit |
| `503` | `WEATHER_PROVIDER_CIRCUIT_OPEN` | Provider calls are paused during recovery |
| `504` | `WEATHER_PROVIDER_TIMEOUT` | Configured provider timeout elapsed |
| `500` | `INTERNAL_ERROR` | Unexpected server error |

Eligible provider failures are attempted no more than the configured total
attempt count. A retained stale weather response may replace a provider error;
location searches and uncached weather requests preserve the error contract.

