# ADR 0002: Phase-aware readiness

- Status: Accepted
- Date: 2026-11-07

## Context

Docker Compose starts Redis in Phase 1, but application-level cache integration
is explicitly deferred to Phase 3.

## Decision

The readiness endpoint checks only successful API initialization during Phase
1. It does not open a Redis connection. Redis receives its own container health
check.

## Alternatives

Probing Redis now would couple API readiness to an unused dependency and would
introduce cache client lifecycle code before its dedicated phase.

## Consequences

The endpoint honestly represents current runtime dependencies. Phase 3 must
revisit readiness semantics when Redis becomes part of request handling.

