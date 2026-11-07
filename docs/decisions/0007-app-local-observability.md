# ADR 0007: App-local metrics and request correlation

- Status: accepted
- Date: 2026-11-07

## Context

Phase 6 requires useful structured diagnostics, request correlation, latency,
cache/provider visibility, and deterministic tests. Global Prometheus collectors
collide when test suites create more than one FastAPI application, while raw URL,
query, or cache-key labels create unsafe metric cardinality.

## Decision

Each FastAPI instance owns a Prometheus `CollectorRegistry` and passes one
metrics facade to HTTP middleware, cache, and provider adapters. HTTP labels use
route templates. Cache and provider labels come from bounded code-owned outcome
sets. `/metrics` is excluded from its own HTTP observations.

A request middleware validates or generates `X-Request-ID`, binds it with
a context variable, measures the full request, echoes it to the client, and emits
a structured completion record. Error handlers add typed error context without
logging request parameters or provider payloads.

## Consequences

- tests can instantiate isolated registries without duplicate collector errors
- logs and client reports can be correlated using one request ID
- latency, error, cache, and provider behavior are queryable with bounded labels
- metric values are process-local and require an explicit multiprocess strategy
  if Phase 7 deploys more than one API worker
- health-only smoke testing provides a stable regression gate but is not a
  substitute for production load and capacity testing
