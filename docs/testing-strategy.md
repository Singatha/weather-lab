# Testing strategy

## Current checks

The web suite uses Vitest, React Testing Library, and user-event to verify
forecast rendering, unit conversion, keyboard suggestion selection, and empty
results through user-visible semantics. Playwright exercises the same core
flows in desktop Chromium and a mobile viewport with network responses mocked
at the browser boundary. Axe scans those rendered views against WCAG 2.0 and
2.1 A/AA rules. ESLint and TypeScript protect source quality and type safety; a
production Vite build verifies bundling.

The API suite uses Pytest and HTTPX's ASGI transport to exercise contracts over
HTTP. Ruff enforces Python linting and formatting, while MyPy runs in strict
mode.

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
contracts, separate HTTP timeouts, and complete lifespan cleanup.

Docker Compose configuration is validated separately so orchestration mistakes
fail before containers are started.

Ordinary tests do not make live Open-Meteo or Redis requests. Provider, API,
component, and browser fixtures remain deterministic. Observability coverage
will be introduced alongside the Phase 6 instrumentation it protects.

