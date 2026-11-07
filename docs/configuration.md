# Configuration

Copy `.env.example` to `.env` for local overrides. Defaults are suitable for
Docker Compose and no secrets are required through Phase 2.

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | API runtime profile | `development` |
| `APP_NAME` | OpenAPI application title | `Weather API` |
| `API_CORS_ORIGINS` | JSON list of allowed browser origins | `["http://localhost:5173"]` |
| `REDIS_URL` | Future cache connection URL | `redis://redis:6379/0` in Compose |
| `OPEN_METEO_FORECAST_URL` | Forecast provider endpoint | Open-Meteo forecast API |
| `OPEN_METEO_GEOCODING_URL` | Location provider endpoint | Open-Meteo geocoding API |
| `WEATHER_PROVIDER_TIMEOUT_SECONDS` | Total provider request timeout | `10` |
| `VITE_API_BASE_URL` | Browser-visible API origin | `http://localhost:8000` |

`REDIS_URL` is configured for orchestration but is not consumed by application
cache logic until Phase 3. Provider URLs are configurable to support tests and
future self-hosting without changing application code.

