# Configuration

Copy `.env.example` to `.env` for local overrides. Defaults are suitable for
Docker Compose development. Production uses `.env.production` plus a file-mounted
Redis password; start from `.env.production.example` and never commit the copy.

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | API runtime profile | `development` |
| `APP_NAME` | OpenAPI application title | `Weather API` |
| `LOG_LEVEL` | Structured application log threshold | `INFO` |
| `API_CORS_ORIGINS` | JSON list of allowed browser origins | `["http://localhost:5173"]` |
| `REDIS_URL` | Cache connection URL | `redis://redis:6379/0` in Compose |
| `REDIS_PASSWORD` | Optional Redis password supplied directly; prefer a file in production | unset |
| `REDIS_PASSWORD_FILE` | Password file inside the API container | unset |
| `REDIS_SOCKET_TIMEOUT_SECONDS` | Redis connect and command timeout | `1` |
| `REDIS_MAX_CONNECTIONS` | Maximum process-local Redis connections | `20` |
| `LOCATION_CACHE_TTL_SECONDS` | Location search freshness and retention | `86400` |
| `WEATHER_CACHE_TTL_SECONDS` | Weather freshness | `900` |
| `WEATHER_CACHE_STALE_TTL_SECONDS` | Total weather retention for stale fallback | `7200` |
| `OPEN_METEO_FORECAST_URL` | Forecast provider endpoint | Open-Meteo forecast API |
| `OPEN_METEO_GEOCODING_URL` | Location provider endpoint | Open-Meteo geocoding API |
| `WEATHER_PROVIDER_CONNECT_TIMEOUT_SECONDS` | Provider socket connection timeout | `3` |
| `WEATHER_PROVIDER_READ_TIMEOUT_SECONDS` | Provider response-chunk read timeout | `10` |
| `WEATHER_PROVIDER_WRITE_TIMEOUT_SECONDS` | Provider request-chunk write timeout | `5` |
| `WEATHER_PROVIDER_POOL_TIMEOUT_SECONDS` | Provider connection-pool acquisition timeout | `3` |
| `WEATHER_PROVIDER_MAX_CONNECTIONS` | Maximum provider HTTP connections | `20` |
| `WEATHER_PROVIDER_MAX_KEEPALIVE_CONNECTIONS` | Maximum idle provider HTTP connections | `10` |
| `WEATHER_PROVIDER_MAX_ATTEMPTS` | Total attempts for an eligible provider call | `3` |
| `WEATHER_PROVIDER_RETRY_BASE_DELAY_SECONDS` | Initial exponential retry delay | `0.2` |
| `WEATHER_PROVIDER_RETRY_MAX_DELAY_SECONDS` | Exponential delay cap before jitter | `2` |
| `WEATHER_PROVIDER_RETRY_JITTER_RATIO` | Maximum positive jitter as a delay fraction | `0.25` |
| `WEATHER_PROVIDER_CIRCUIT_FAILURE_THRESHOLD` | Failed logical calls before opening a circuit | `5` |
| `WEATHER_PROVIDER_CIRCUIT_RECOVERY_SECONDS` | Open duration before one half-open probe | `30` |
| `API_RATE_LIMIT_REQUESTS` | Requests allowed per client and window | `60` |
| `API_RATE_LIMIT_WINDOW_SECONDS` | Fixed API rate-limit window | `60` |
| `VITE_API_BASE_URL` | Browser-visible API origin | `http://localhost:8000` |

The stale weather TTL must be greater than or equal to the fresh weather TTL.
Provider URLs are configurable to support tests and future self-hosting without
changing application code.

The retry maximum delay must be at least the base delay. Keepalive connections
must not exceed the total provider connection limit. `WEATHER_PROVIDER_MAX_ATTEMPTS`
includes the first attempt, so the default permits at most two retries.

`REDIS_PASSWORD` and `REDIS_PASSWORD_FILE` are mutually exclusive. Production
sets only `REDIS_PASSWORD_FILE=/run/secrets/redis_password`; Docker Compose mounts
that path read-only for API and Redis.

## Production orchestration variables

These variables are consumed by `compose.production.yml`, not directly by the
FastAPI settings model.

| Variable | Purpose | Example/default |
| --- | --- | --- |
| `APP_DOMAIN` | Caddy HTTPS hostname | `localhost` for smoke tests |
| `PUBLIC_ORIGIN` | Matching browser origin used for CORS | `https://localhost` |
| `HTTP_PORT` | Host HTTP/ACME port | `80` |
| `HTTPS_PORT` | Host HTTPS and HTTP/3 port | `443` |
| `IMAGE_PREFIX` | Image registry/repository prefix | `weather-lab` locally |
| `IMAGE_TAG` | Exact API/web tag | `local` or immutable SHA |
| `REDIS_PASSWORD_FILE_PATH` | Host path used as a Compose secret | `./secrets/redis_password.txt` |
| `REDIS_MAXMEMORY` | Redis cache memory ceiling | `256mb` |

The production web bundle uses an empty `VITE_API_BASE_URL`, making browser API
requests relative to the public HTTPS origin. Build-time frontend values are not
runtime secrets.

