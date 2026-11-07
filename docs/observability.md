# Observability

## Structured logs and request correlation

Application records are emitted as one JSON object per line. Every HTTP request
receives an `X-Request-ID`; a valid caller-supplied value is preserved, otherwise
the API generates a UUID. The same value is returned in the response and bound
to request, validation, and application-error logs.

Request IDs are limited to 128 ASCII letters, digits, dots, underscores, and
hyphens. This prevents untrusted header values from injecting log lines. Logs
include a UTC timestamp, severity, logger, event, request ID, method, route,
status, and duration where applicable. Provider queries, coordinates, and cache
keys are intentionally excluded.

Set `LOG_LEVEL` to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. The default
is `INFO`.

## Prometheus metrics

`GET /metrics` exposes an app-local Prometheus registry. The scrape itself is
excluded from HTTP metrics. Labels use route templates and bounded outcomes to
avoid unbounded cardinality.

| Metric | Type | Purpose |
| --- | --- | --- |
| `weather_http_requests_total` | counter | Requests by method, route, and status |
| `weather_http_errors_total` | counter | Responses with status 400 or greater |
| `weather_http_request_duration_seconds` | histogram | End-to-end API latency |
| `weather_cache_operations_total` | counter | Cache hit, miss, stale, write, and failure outcomes |
| `weather_provider_requests_total` | counter | Forecast/geocoding calls by bounded outcome |
| `weather_provider_request_duration_seconds` | histogram | Logical provider latency including retries |

The custom registry avoids duplicate collectors when tests instantiate multiple
applications. A future multi-worker production deployment must configure the
Prometheus client's multiprocess mode or use one worker per metrics registry.

Useful PromQL examples:

```promql
histogram_quantile(0.95, sum by (le, route) (rate(weather_http_request_duration_seconds_bucket[5m])))
sum by (result) (rate(weather_cache_operations_total{operation="get"}[5m]))
sum by (operation, outcome) (rate(weather_provider_requests_total[5m]))
```

## Performance smoke target

The deterministic smoke runner targets `/health/live`, so it measures local API
and middleware overhead without network-provider variance:

```bash
docker compose up --detach --wait api
docker compose exec -T api python -m performance.smoke \
  --base-url http://127.0.0.1:8000 \
  --requests 100 --concurrency 20 --max-p95-ms 250
```

The CI target is zero errors and p95 below 250 ms. A local Docker run on
2026-11-07 measured 781.6 requests/second, p50 14.52 ms, p95 61.26 ms, and p99
73.28 ms across 100 requests at concurrency 20. This is a regression baseline,
not a production SLO; deployment-phase load tests must use representative
hardware, traffic, and weather endpoints.
