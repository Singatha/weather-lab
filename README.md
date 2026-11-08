# Weather Lab

A production-minded full-stack weather application built as a backend
engineering learning project. This repository contains the completed **Phase 7:
Deployment and Documentation** scope.

## What is implemented

- responsive React 19, TypeScript, Vite, Tailwind CSS, and TanStack Query weather dashboard
- debounced, keyboard-accessible location suggestions backed by FastAPI
- current conditions, four weather metrics, seven-day cards, and day-selectable hourly forecasts
- independent and one-click metric/imperial measurement controls
- supplied local fonts, backgrounds, weather icons, loading, empty, stale, and API error states
- FastAPI service with typed Pydantic Settings
- `GET /health/live` and `GET /health/ready`
- `GET /api/v1/locations/search?q=Berlin`
- `GET /api/v1/weather?latitude=52.52&longitude=13.41`
- Open-Meteo adapter behind an application-owned provider protocol
- Normalized current, hourly, and seven-day weather response schemas
- IANA-timezone-aware timestamps and WMO condition mapping
- Consistent validation and upstream-provider error responses
- Redis-backed location and weather caching with configurable TTLs
- fresh, stale, miss, hit, and cache-bypass weather metadata
- stale weather fallback when Open-Meteo is unavailable
- graceful cache degradation and concurrent request coalescing
- separate provider connection, read, write, and pool timeouts
- bounded transient retries with exponential backoff and jitter
- independent forecast and geocoding circuit breakers with half-open recovery
- Redis-backed API rate limiting with a process-local degradation fallback
- deterministic graceful shutdown for HTTP and Redis resources
- JSON application logs with correlated `X-Request-ID` response headers
- Prometheus HTTP, error, cache, and provider latency/outcome metrics
- deterministic performance smoke target with a documented local baseline
- Vitest/Testing Library, Playwright desktop/mobile, and Pytest test suites
- CI coverage reports for both applications
- ESLint, TypeScript, Ruff, and strict MyPy checks
- Development and production Docker build stages
- Docker Compose environment with web, API, and Redis services
- GitHub Actions validation for both applications and Compose
- hardened, non-root production API and web images with built-in health checks
- provider-neutral production Compose stack with private origin/data networks
- same-origin routing and automatic HTTPS through Caddy
- authenticated, persistent, memory-bounded Redis configured through a file secret
- GHCR release images, immutable SHA tags, attestations, and optional SSH deployment
- deployment, rollback, backup, monitoring, secret-rotation, and incident runbooks

## Prerequisites

- Node.js 22+ and npm 10+
- Python 3.12+
- Docker with Docker Compose

Docker is the easiest path if Python 3.12 is not installed on the host.

## Quick start with Docker

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Web: <http://localhost:5173>
- API docs: <http://localhost:8000/docs>
- Liveness: <http://localhost:8000/health/live>
- Readiness: <http://localhost:8000/health/ready>
- Metrics: <http://localhost:8000/metrics>
- Location search: <http://localhost:8000/api/v1/locations/search?q=Berlin>
- Berlin weather: <http://localhost:8000/api/v1/weather?latitude=52.52&longitude=13.41>

Stop the environment with:

```bash
docker compose down
```

Add `--volumes` only when you intentionally want to remove local Redis and
Node dependency volumes.

## Production-like deployment

No cloud provider is assumed. The portable stack runs on any suitable Linux
Docker host and uses local HTTPS on `localhost` for verification:

```bash
cp .env.production.example .env.production
mkdir -p secrets
umask 077
openssl rand -hex 32 > secrets/redis_password.txt
docker compose --env-file .env.production -f compose.production.yml \
  up --build --detach --wait
curl --fail --insecure https://localhost/health/live
```

Only Caddy publishes ports. The built frontend calls the API on the same HTTPS
origin; API port 8000, Redis port 6379, metrics, and API documentation stay
private. For a public hostname, configure DNS, set `APP_DOMAIN` and
`PUBLIC_ORIGIN`, and open TCP 80/443 plus UDP 443. See the
[deployment guide](docs/deployment.md) before using a remote host.

## Run on the host

### Web

```bash
npm install
npm run dev:web
```

### API

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e 'apps/api[dev]'
.venv/bin/uvicorn app.main:app --reload --app-dir apps/api
```

On Windows PowerShell, activate the virtual environment and use `python -m`
commands instead of the Unix-style `.venv/bin/...` paths.

## Quality checks

Install the Playwright browser once before running the end-to-end suite:

```bash
npx playwright install chromium
```

```bash
# Web
npm run lint:web
npm run typecheck:web
npm run test:web
npm run test:coverage:web
npm run test:e2e
npm run build:web

# API
cd apps/api
../../.venv/bin/ruff check app tests performance
../../.venv/bin/ruff format --check app tests performance
../../.venv/bin/mypy app tests performance
../../.venv/bin/pytest
../../.venv/bin/pytest --cov=app --cov-report=term-missing

# Orchestration
cd ../..
docker compose config --quiet
docker compose --env-file .env.production.example -f compose.production.yml config --quiet
docker compose up --detach --wait api
docker compose exec -T api python -m performance.smoke --base-url http://127.0.0.1:8000
```

Equivalent grouped commands are available as `make web-check`,
`make api-check`, and `make compose-config`.

## Repository structure

```text
.
├── apps/
│   ├── api/                 # FastAPI application and tests
│   └── web/                 # React application and tests
├── docs/                    # Current requirements, architecture, and ADRs
├── infra/                   # Docker, Caddy, and Nginx production configuration
├── .github/workflows/       # CI plus image release/deployment automation
├── compose.production.yml   # Portable production topology
├── docker-compose.yml
└── Makefile
```

## Configuration

Copy `.env.example` to `.env` for development or `.env.production.example` to
`.env.production` for production. See [configuration](docs/configuration.md) for
the complete table. Production requires a random Redis password under the
ignored `secrets/` directory; never commit the environment copy or secret.

## Documentation

- [Implemented requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [API contract](docs/api-contract.md)
- [Testing strategy](docs/testing-strategy.md)
- [Observability and performance](docs/observability.md)
- [Portable deployment](docs/deployment.md)
- [Operations runbook](docs/operations.md)
- [Architecture decisions](docs/decisions/0001-modular-monorepo.md)
- [Provider and timezone decision](docs/decisions/0003-provider-boundary-and-timezones.md)
- [Caching and stale fallback decision](docs/decisions/0004-cache-freshness-and-fallback.md)
- [Frontend data and unit boundaries](docs/decisions/0005-frontend-data-and-unit-boundaries.md)
- [Provider resilience and API rate limiting](docs/decisions/0006-provider-resilience-and-rate-limiting.md)
- [App-local observability](docs/decisions/0007-app-local-observability.md)
- [Portable production deployment](docs/decisions/0008-portable-production-compose.md)

## Git initialization

If this directory was supplied without repository metadata, initialize it once:

```bash
git init
```

## Deployment status

The repository includes a tested production-like deployment and cloud-neutral
release pipeline. It does not provision or mutate external infrastructure. A
public deployment still requires an explicitly approved provider, domain, host,
firewall policy, and GitHub production-environment configuration.

## Data attribution

Weather data is provided by [Open-Meteo](https://open-meteo.com/). Location
search data is based on GeoNames and delivered through the Open-Meteo
Geocoding API. Review their current licensing terms before commercial use.

