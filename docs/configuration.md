# Configuration

Copy `.env.example` to `.env` for local overrides. Defaults are suitable for
Docker Compose and no secrets are required through Phase 4.

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | API runtime profile | `development` |
| `APP_NAME` | OpenAPI application title | `Weather API` |
| `API_CORS_ORIGINS` | JSON list of allowed browser origins | `["http://localhost:5173"]` |
| `REDIS_URL` | Cache connection URL | `redis://redis:6379/0` in Compose |
| `REDIS_SOCKET_TIMEOUT_SECONDS` | Redis connect and command timeout | `1` |
| `REDIS_MAX_CONNECTIONS` | Maximum process-local Redis connections | `20` |
| `LOCATION_CACHE_TTL_SECONDS` | Location search freshness and retention | `86400` |
| `WEATHER_CACHE_TTL_SECONDS` | Weather freshness | `900` |
| `WEATHER_CACHE_STALE_TTL_SECONDS` | Total weather retention for stale fallback | `7200` |
| `OPEN_METEO_FORECAST_URL` | Forecast provider endpoint | Open-Meteo forecast API |
| `OPEN_METEO_GEOCODING_URL` | Location provider endpoint | Open-Meteo geocoding API |
| `WEATHER_PROVIDER_TIMEOUT_SECONDS` | Total provider request timeout | `10` |
| `VITE_API_BASE_URL` | Browser-visible API origin | `http://localhost:8000` |

The stale weather TTL must be greater than or equal to the fresh weather TTL.
Provider URLs are configurable to support tests and future self-hosting without
changing application code.

