# Testing strategy

## Phase 1 checks

The web suite uses Vitest and React Testing Library to verify the application
shell through user-visible semantics. ESLint and TypeScript protect source
quality and type safety; a production Vite build verifies bundling.

The API suite uses Pytest and FastAPI's test client to exercise both health
contracts over HTTP. Ruff enforces Python linting and formatting, while MyPy
runs in strict mode.

Docker Compose configuration is validated separately so orchestration mistakes
fail before containers are started.

## Later phases

Provider calls will use deterministic HTTP fixtures and test doubles. Ordinary
tests will not make live Open-Meteo requests. Cache, resilience, component, and
end-to-end coverage will be introduced alongside the behavior they protect.

