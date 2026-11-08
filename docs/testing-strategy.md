# Testing strategy

## Automated checks

The web suite uses Vitest, React Testing Library, and user-event to verify
forecast rendering, loading, stale-data context, API retry, unit conversion,
keyboard suggestion selection, day selection, and empty results through
user-visible semantics. Playwright exercises the critical flows in desktop
Chromium and a mobile viewport with network responses mocked
at the browser boundary. Axe scans those rendered views against WCAG 2.0 and
2.1 A/AA rules. ESLint and TypeScript protect source quality and type safety; a
production Vite build verifies bundling.

The API suite uses Pytest and HTTPX's ASGI transport to exercise contracts over
HTTP. It verifies request-ID propagation, JSON log fields, metrics exposition,
cache labels, and provider success/failure latency. Ruff enforces Python linting
and formatting, while MyPy runs in strict mode.

Provider tests use HTTPX `MockTransport` with deterministic Open-Meteo
payloads. They verify query parameters, response normalization, timezone
localization, WMO mapping, malformed time-series rejection, timeouts, and rate
limits. Route tests inject a stub provider through the service dependency and
verify success, validation, error, and OpenAPI contracts.

Phase 3 cache tests use an in-memory backend and controllable clock to verify
fresh and stale transitions, retention TTLs, corrupt values, Redis failures,
cache metadata, location caching, and concurrent miss coalescing. A separate
manual Compose smoke test validates the redis-py adapter against real Redis.

Phase 5 failure simulations use deterministic clocks, sleepers, randomizers,
HTTPX transports, and in-memory counters. They cover retry eligibility and
limits, exact backoff delays, every circuit transition, one-probe half-open
behavior, stale-data permissions, Redis rate-limit fallback, `429` middleware
contracts, separate HTTP timeouts, and complete lifespan cleanup. Phase 6
extends these boundaries without making live provider calls.

Vitest V8 coverage and Pytest branch coverage run in CI and are uploaded as
`web-coverage` and `api-coverage` artifacts. The Phase 6 baseline is 87.22%
web statement coverage and 94% API coverage.

The Compose CI job starts API plus Redis and runs 100 concurrent-scheduled
health requests at concurrency 20. It requires zero errors and p95 under 250 ms.
See [observability](observability.md) for the command, measured baseline, metric
catalog, and interpretation limits.

Docker Compose configuration is validated separately so orchestration mistakes
fail before containers are started.

Phase 7 adds a production-stack CI job. It generates an ephemeral Redis secret,
builds the production API and web targets, waits for Redis, API, web, and Caddy
health checks, verifies the frontend and API through local HTTPS, and confirms
that the public edge rejects `/metrics`. The secret and named volumes are removed
when the job finishes.

Ordinary tests do not make live Open-Meteo requests. Provider, API, component,
and browser fixtures remain deterministic. The performance smoke uses real
Redis only for readiness before targeting the provider-independent liveness
endpoint. Live provider testing remains an explicit manual suite outside CI.

