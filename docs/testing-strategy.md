# Testing strategy

## Current checks

The web suite uses Vitest and React Testing Library to verify the application
shell through user-visible semantics. ESLint and TypeScript protect source
quality and type safety; a production Vite build verifies bundling.

The API suite uses Pytest and HTTPX's ASGI transport to exercise contracts over
HTTP. Ruff enforces Python linting and formatting, while MyPy runs in strict
mode.

Phase 2 provider tests use HTTPX `MockTransport` with deterministic Open-Meteo
payloads. They verify query parameters, response normalization, timezone
localization, WMO mapping, malformed time-series rejection, timeouts, and rate
limits. Route tests inject a stub provider through the service dependency and
verify success, validation, error, and OpenAPI contracts.

Docker Compose configuration is validated separately so orchestration mistakes
fail before containers are started.

## Later phases

Ordinary tests do not make live Open-Meteo requests. Cache, resilience,
component, and end-to-end coverage will be introduced alongside the behavior
they protect.

