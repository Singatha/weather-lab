# ADR 0006: Provider resilience and API rate limiting

- Status: accepted
- Date: 2026-11-07

## Context

Provider latency, transient network failures, upstream overload, and abusive
clients can exhaust API resources. Retrying indiscriminately can amplify an
outage, while coupling stale-cache policy to transport code can serve data in
cases the application did not authorize.

## Decision

HTTPX uses explicit connection, read, write, and pool timeouts. Provider calls
retry only timeouts, transport failures, upstream rate limits, HTTP 408/425,
and 5xx responses. The total attempt count is finite. Delay grows exponentially,
is capped, and receives bounded positive jitter.

Forecast and geocoding have separate consecutive-failure circuit breakers. A
logical call records one failure only after its retries are exhausted. An open
circuit fails fast, then permits one half-open probe after the recovery period.
Success closes the circuit; failure reopens it.

`WeatherService` remains the only layer allowed to select retained stale
weather. Any typed provider failure, including an open circuit, may use stale
weather when the cache still retains it. No stale location fallback is added.

Versioned API routes use an IP-scoped fixed-window limiter. Redis executes the
increment and expiry atomically through Lua. A Redis outage falls back to an
in-process counter; this is intentionally weaker across multiple workers but
preserves local protection and API availability.

## Consequences

- provider failures have a strict upper attempt and timeout bound
- geocoding instability does not open the forecast circuit, or vice versa
- retry storms are reduced during sustained outages
- stale behavior remains explicit and testable at the service boundary
- horizontally scaled rate limits are shared while Redis is healthy
- deployment must configure trusted proxy handling before using forwarded IPs
