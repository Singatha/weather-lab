# Weather API

FastAPI service for Weather Lab. Phase 3 exposes health, location search, and
normalized weather forecast endpoints backed by an asynchronous Open-Meteo
adapter and Redis cache.

The adapter requests canonical metric data and maps provider payloads into
application-owned Pydantic schemas. Automated tests use deterministic HTTPX
mock transports and never call the live provider.

Location searches are cached for 24 hours. Weather is fresh for 15 minutes and
retained for up to two hours so an upstream failure can return a clearly marked
stale response. Redis failures bypass caching rather than failing weather
requests.

