# Weather API

FastAPI service for Weather Lab. Phase 2 exposes health, location search, and
normalized weather forecast endpoints backed by an asynchronous Open-Meteo
adapter. Redis caching is intentionally deferred to Phase 3.

The adapter requests canonical metric data and maps provider payloads into
application-owned Pydantic schemas. Automated tests use deterministic HTTPX
mock transports and never call the live provider.

