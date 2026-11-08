# Implemented requirements through Phase 7

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

## Frontend application

- supplied Frontend Mentor desktop and mobile design reproduced with bundled assets and fonts
- debounced FastAPI location search with suggestions, empty results, and in-progress feedback
- keyboard navigation for suggestions and semantic, labelled controls
- current weather, feels-like, humidity, wind, and precipitation metrics
- seven-day forecasts and day-selectable hourly forecasts
- client-side metric and imperial conversions from canonical backend units
- responsive desktop, tablet, and mobile layouts from 320 pixels upward
- weather loading skeleton, provider error/retry, and stale-cache messaging
- deterministic component tests plus desktop and mobile Playwright flows

## Resilience engineering

- independent HTTP connection, read, write, and pool timeouts
- finite retries only for timeouts, transport errors, rate limits, and transient statuses
- capped exponential backoff with configurable positive jitter
- independent forecast and geocoding consecutive-failure circuit breakers
- open, half-open single-probe, recovered, and reopened circuit transitions
- retained stale weather returned for provider and open-circuit failures only
- atomic Redis fixed-window API rate limiting by direct client address
- process-local rate-limit fallback when Redis is unavailable
- consistent `429` error envelopes and rate-limit response headers
- lifespan-owned HTTP and Redis clients with best-effort complete shutdown
- deterministic failure simulations for every Phase 5 policy

## Testing and observability

- expanded unit, integration, API contract, component, and browser coverage
- loading, stale-data, empty, validation, provider failure, and retry scenarios
- desktop and mobile Chromium E2E execution with deterministic network mocks
- API and web coverage reports retained as CI artifacts
- JSON application logs with bounded diagnostic context
- validated/generated request IDs echoed in every response and correlated in logs
- Prometheus HTTP request, error, and latency metrics using route templates
- cache operation and provider outcome/latency metrics without sensitive keys
- deterministic performance runner with a zero-error, p95-under-250-ms CI target
- live provider requests kept outside the ordinary automated suite

## Deployment and operations

- separate production Docker targets for non-root API and static web processes
- provider-neutral production Compose topology with no source bind mounts
- same-origin frontend/API routing through a single Caddy HTTPS edge
- automatic public-certificate provisioning and HTTP-to-HTTPS redirects
- private API and Redis networks with no direct host port publication
- authenticated, memory-bounded Redis with AOF persistence on a named volume
- file-mounted Redis credentials supported without secret environment variables
- read-only root filesystems, dropped capabilities, and no-new-privileges controls
- image, service, and routed liveness/readiness health checks
- GHCR image publication with immutable SHA tags and artifact attestations
- optional protected-environment SSH deployment to a pre-provisioned Docker host
- documented bootstrap, monitoring, backup, rotation, rollback, and incident flows
- CI production-stack build and HTTPS smoke verification

## Future infrastructure decisions

- cloud provider and infrastructure-as-code implementation
- highly available multi-host orchestration and managed Redis
- production dashboards, alert delivery, retention, and centralized log storage
- multi-worker or horizontal metric aggregation

These decisions require traffic, availability, budget, jurisdiction, and hosting
requirements that are outside the approved provider-neutral Phase 7 scope.

