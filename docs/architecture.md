# Architecture

## Phase 2 runtime

```mermaid
flowchart LR
    Browser[Browser] -->|HTTP :5173| Web[React + Vite]
    Web -. Phase 4 REST calls .->|HTTP :8000| Routes[FastAPI routes]
    Routes --> Service[Weather service]
    Service --> Provider[Weather provider protocol]
    Provider -->|HTTPS| OpenMeteo[Open-Meteo APIs]
    Service -. Phase 3 .-> Redis[(Redis)]
```

The repository is a modular monorepo with independently testable web and API
applications. Docker Compose supplies a reproducible local environment while
each application can also run directly on the host.

## Boundaries

- `apps/web` owns browser rendering and frontend server state.
- `apps/api/app/api` owns versioned HTTP routing and dependency wiring.
- `apps/api/app/services` owns application use cases.
- `apps/api/app/providers` owns the provider protocol and Open-Meteo translation.
- `apps/api/app/schemas` owns stable application-facing contracts.
- `infra/docker` owns container build definitions.
- `docs` records current behavior and decisions.

The frontend never consumes Open-Meteo payloads directly. Provider responses
are validated and translated before reaching routes. Cache modules remain
absent until Phase 3 gives them real behavior.

