# ADR 0004: Cache freshness, stale retention, and graceful degradation

- Status: Accepted
- Date: 2026-11-07

## Context

Weather data is requested frequently but changes less often than users refresh
the page. Open-Meteo or Redis can fail independently, and cache failures must
not automatically make fresh provider data unavailable.

## Decision

Use cache-aside reads through an application-owned `CacheService`. Store a JSON
envelope containing the validated application model, `stored_at`, and
`fresh_until`. Redis retains weather entries for the configured stale horizon,
while the envelope determines whether the value is fresh.

- Location searches are fresh and retained for 24 hours.
- Weather is fresh for 15 minutes and retained for up to two hours total.
- Fresh values return immediately.
- Stale weather is returned only after a typed provider failure.
- Redis read or write failures fall through to the provider.
- Same-key misses are coalesced within one process and recheck Redis before
  calling the provider.

## Alternatives

- Separate fresh and stale keys simplify freshness checks but duplicate payloads
  and require coordinated writes.
- Making Redis a hard dependency would provide strict cache guarantees but
  reduce weather availability during cache outages.
- A distributed Redis lock could coordinate every API instance but introduces
  lock expiry and ownership failure modes. It is deferred until measured load
  justifies it.

## Consequences

The API can distinguish hits, misses, stale responses, and bypasses while
remaining available during Redis failures. Per-process counters and coalescing
are not globally aggregated; Phase 6 observability can export shared metrics,
and later load testing can determine whether distributed coalescing is needed.

