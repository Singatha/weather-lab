# Phase 1 requirements

## Scope

Phase 1 establishes a runnable, testable development foundation. It includes:

- a React, TypeScript, Vite, Tailwind CSS, and TanStack Query web shell;
- a Python 3.12 FastAPI service configured with Pydantic Settings;
- liveness and readiness HTTP endpoints;
- Vitest, Pytest, Ruff, MyPy, and ESLint configuration;
- local Docker images and Docker Compose orchestration with Redis;
- a basic CI workflow and development documentation.

## Explicitly deferred

The following requirements are documented in the master brief but are not
implemented in Phase 1:

- Open-Meteo and geocoding integration;
- application-level Redis caching;
- weather API endpoints and normalized forecast schemas;
- the supplied Frontend Mentor dashboard design;
- retries, circuit breaking, rate limiting, and observability;
- production deployment.

This boundary preserves a working deliverable while keeping later design and
reliability decisions tied to concrete use cases.

