# API contract — Phase 1

## `GET /health/live`

Confirms that the FastAPI process is running and can serve requests.

Response `200 OK`:

```json
{"status": "ok"}
```

## `GET /health/ready`

Confirms that Phase 1 application initialization completed. Redis is not
probed yet because the API does not depend on it until Phase 3.

Response `200 OK`:

```json
{"status": "ready"}
```

Interactive OpenAPI documentation is available at `/docs` during development.
Versioned location and weather endpoints are intentionally deferred to Phase 2.

