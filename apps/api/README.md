# Weather API

FastAPI service for Weather Lab. Phase 5 exposes health, location search, and
normalized weather forecast endpoints backed by an asynchronous Open-Meteo
adapter, Redis cache, and resilience policies.

The adapter requests canonical metric data and maps provider payloads into
application-owned Pydantic schemas. Automated tests use deterministic HTTPX
mock transports and never call the live provider.

Location searches are cached for 24 hours. Weather is fresh for 15 minutes and
retained for up to two hours so an upstream failure can return a clearly marked
stale response. Redis failures bypass caching rather than failing weather
requests.

Provider calls use separate connection, read, write, and pool timeouts. Only
timeouts, transport failures, provider rate limits, and transient upstream HTTP
statuses are retried. Retries are finite and use capped exponential backoff with
jitter. Forecast and geocoding use independent consecutive-failure circuit
breakers so one provider operation cannot unnecessarily block the other.

Versioned API routes use a per-client fixed-window rate limit backed by an
atomic Redis script. Redis failures degrade to a process-local counter. Shared
HTTP and Redis clients are closed through FastAPI's lifespan context.

