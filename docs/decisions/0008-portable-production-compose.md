# ADR 0008: Portable single-host production deployment

- Status: accepted
- Date: 2026-11-08

## Context

Phase 7 requires deployable backend, frontend, Redis, HTTPS, health checks, and
CI/CD, but no cloud provider has been approved. The deployment must therefore be
testable and operational without embedding provider-specific infrastructure.

## Decision

Use a separate production Compose definition. Caddy is the only public service
and terminates automatic HTTPS. It routes same-origin API and health paths to a
single FastAPI worker and all other paths to an immutable Nginx SPA image. Redis
and origins remain on private networks with no host ports.

API and web images run as non-root users with read-only root filesystems,
dropped capabilities, explicit health checks, and temporary writable mounts.
Redis is authenticated through a Compose file secret, memory-bounded with
`allkeys-lru`, and persisted with AOF on a named volume.

GitHub Actions publishes immutable API/web images and attestations to GHCR. An
optional protected-environment job deploys exact SHA tags over verified SSH to
any pre-provisioned Docker host. Infrastructure provisioning remains deferred
until the user approves a provider.

## Consequences

- the complete production topology is reproducible locally and in CI
- frontend and API share one HTTPS origin and need no production CORS exception
- only the edge owns public ports; metrics and documentation remain internal
- host configuration and secrets survive image rollbacks
- the deployment is limited to one host and one API worker
- high availability, managed backups, autoscaling, and infrastructure as code
  depend on a future provider decision
