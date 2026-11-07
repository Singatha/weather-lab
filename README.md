# Weather Lab

A production-minded full-stack weather application built as a backend
engineering learning project. This repository currently contains **Phase 3:
Redis Caching**.

## What is implemented

- React 19, TypeScript, Vite, Tailwind CSS, and TanStack Query application shell
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
- Vitest/Testing Library and Pytest test suites
- ESLint, TypeScript, Ruff, and strict MyPy checks
- Development and production Docker build stages
- Docker Compose environment with web, API, and Redis services
- GitHub Actions validation for both applications and Compose

The final weather dashboard is intentionally deferred to Phase 4.

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
- Location search: <http://localhost:8000/api/v1/locations/search?q=Berlin>
- Berlin weather: <http://localhost:8000/api/v1/weather?latitude=52.52&longitude=13.41>

Stop the environment with:

```bash
docker compose down
```

Add `--volumes` only when you intentionally want to remove local Redis and
Node dependency volumes.

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

```bash
# Web
npm run lint:web
npm run typecheck:web
npm run test:web
npm run build:web

# API
cd apps/api
../../.venv/bin/ruff check app tests
../../.venv/bin/ruff format --check app tests
../../.venv/bin/mypy app tests
../../.venv/bin/pytest

# Orchestration
cd ../..
docker compose config --quiet
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
├── infra/docker/            # Container build definitions
├── .github/workflows/ci.yml # Continuous integration
├── docker-compose.yml
└── Makefile
```

## Configuration

Copy `.env.example` to `.env` and override values as needed. See
[configuration](docs/configuration.md) for the complete configuration table. Never
commit real credentials; this phase requires none.

## Documentation

- [Implemented requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [API contract](docs/api-contract.md)
- [Testing strategy](docs/testing-strategy.md)
- [Architecture decisions](docs/decisions/0001-modular-monorepo.md)
- [Provider and timezone decision](docs/decisions/0003-provider-boundary-and-timezones.md)
- [Caching and stale fallback decision](docs/decisions/0004-cache-freshness-and-fallback.md)

## Git initialization

If this directory was supplied without repository metadata, initialize it once:

```bash
git init
```

## Next phase

Phase 4 will implement the supplied Frontend Mentor weather interface, location
suggestions, forecast views, unit switching, responsive behavior, and browser
tests. It should begin only after explicit approval.

## Data attribution

Weather data is provided by [Open-Meteo](https://open-meteo.com/). Location
search data is based on GeoNames and delivered through the Open-Meteo
Geocoding API. Review their current licensing terms before commercial use.

