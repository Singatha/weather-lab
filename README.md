# Weather Lab

A production-minded full-stack weather application built as a backend
engineering learning project. This repository currently contains **Phase 1:
Project Foundation** only.

## What is implemented

- React 19, TypeScript, Vite, Tailwind CSS, and TanStack Query application shell
- FastAPI service with typed Pydantic Settings
- `GET /health/live` and `GET /health/ready`
- Vitest/Testing Library and Pytest test suites
- ESLint, TypeScript, Ruff, and strict MyPy checks
- Development and production Docker build stages
- Docker Compose environment with web, API, and Redis services
- GitHub Actions validation for both applications and Compose

Open-Meteo integration, caching behavior, and the final weather dashboard are
intentionally not part of this phase.

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
[configuration](docs/configuration.md) for the complete Phase 1 table. Never
commit real credentials; this phase requires none.

## Documentation

- [Phase 1 requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [API contract](docs/api-contract.md)
- [Testing strategy](docs/testing-strategy.md)
- [Architecture decisions](docs/decisions/0001-modular-monorepo.md)

## Git initialization

If this directory was supplied without repository metadata, initialize it once:

```bash
git init
```

## Next phase

Phase 2 will introduce the Open-Meteo provider abstraction, geocoding and
weather endpoints, normalized schemas, timezone handling, and provider tests.
It should begin only after explicit approval.

