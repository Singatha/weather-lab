# Architecture

## Phase 1 runtime

```mermaid
flowchart LR
    Browser[Browser] -->|HTTP :5173| Web[React + Vite]
    Web -. future REST calls .->|HTTP :8000| API[FastAPI]
    API -. Phase 3 .-> Redis[(Redis)]
```

The repository is a modular monorepo with independently testable web and API
applications. Docker Compose supplies a reproducible local environment while
each application can also run directly on the host.

## Boundaries

- `apps/web` owns browser rendering and frontend server state.
- `apps/api` owns HTTP contracts, runtime configuration, and future business
  logic.
- `infra/docker` owns container build definitions.
- `docs` records current behavior and decisions.

The API currently has one small route module. Provider, service, cache, and
schema packages will be added only when their phases provide real behavior.

