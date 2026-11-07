# Architecture

## Phase 4 runtime

```mermaid
flowchart LR
    Browser[Browser] --> Web[React + TanStack Query]
    Web -->|Versioned REST / HTTP :8000| Routes[FastAPI routes]
    Routes --> Service[Weather service]
    Service --> Cache[Cache service]
    Cache --> Redis[(Redis)]
    Service --> Provider[Weather provider protocol]
    Provider -->|HTTPS| OpenMeteo[Open-Meteo APIs]
```

The repository is a modular monorepo with independently testable web and API
applications. Docker Compose supplies a reproducible local environment while
each application can also run directly on the host.

## Boundaries

- `apps/web` owns browser rendering and frontend server state.
- `apps/api/app/api` owns versioned HTTP routing and dependency wiring.
- `apps/api/app/services` owns application use cases.
- `apps/api/app/cache` owns keys, serialization, freshness, metrics, Redis, and
  request coalescing.
- `apps/api/app/providers` owns the provider protocol and Open-Meteo translation.
- `apps/api/app/schemas` owns stable application-facing contracts.
- `infra/docker` owns container build definitions.
- `docs` records current behavior and decisions.

The service uses cache-aside reads. Fresh Redis values return immediately.
Stale weather values are retained but used only after a provider failure. Cache
I/O failures fall through to Open-Meteo. Same-key misses are coalesced within
each API process and recheck Redis after acquiring the lock.

The browser treats FastAPI as its only weather data source. TanStack Query owns
location and forecast request state and cancellation. The API remains canonical
in Celsius, km/h, and millimeters; pure frontend formatters apply the selected
display units without issuing redundant weather requests.

