# Configuration

Copy `.env.example` to `.env` for local overrides. Defaults are suitable for
Docker Compose and no secrets are required in Phase 1.

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | API runtime profile | `development` |
| `APP_NAME` | OpenAPI application title | `Weather API` |
| `API_CORS_ORIGINS` | JSON list of allowed browser origins | `["http://localhost:5173"]` |
| `REDIS_URL` | Future cache connection URL | `redis://redis:6379/0` in Compose |
| `VITE_API_BASE_URL` | Browser-visible API origin | `http://localhost:8000` |

`REDIS_URL` is configured now for orchestration but is not consumed by cache
logic until Phase 3.

