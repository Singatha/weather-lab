# Implemented requirements through Phase 3

## Project foundation

- React, TypeScript, Vite, Tailwind CSS, and TanStack Query web shell
- Python 3.12 FastAPI service configured with Pydantic Settings
- liveness and readiness endpoints
- Vitest, Pytest, Ruff, MyPy, and ESLint configuration
- local Docker images and Docker Compose orchestration with Redis
- basic CI workflow and development documentation

## Weather API integration

- asynchronous Open-Meteo forecast and geocoding integration
- provider protocol isolating vendor response formats
- versioned location search and weather endpoints
- normalized location, current, hourly, daily, unit, and metadata schemas
- coordinate and search-query validation
- WMO weather descriptions and UI-oriented categories
- IANA timezone localization for current, hourly, sunrise, and sunset values
- structured validation, timeout, rate-limit, availability, and response errors
- deterministic route, provider, schema, and mapping tests

## Redis caching

- asynchronous redis-py integration with explicit lifespan cleanup
- deterministic, versioned location and coordinate cache keys
- 24-hour location search caching
- 15-minute fresh weather caching with up to two-hour retention
- stale weather fallback only when the provider fails
- Redis failure bypass for both reads and writes
- cache hit, miss, stale, write, and error counters
- per-process same-key request coalescing
- readiness reporting for healthy or degraded Redis
- deterministic cache, failure, TTL, and concurrency tests

## Explicitly deferred

- the supplied Frontend Mentor dashboard design
- retries, circuit breaking, rate limiting, and observability
- production deployment

This boundary keeps Phase 3 independently runnable while preserving the final
interface and resilience policies for their dedicated phases.

