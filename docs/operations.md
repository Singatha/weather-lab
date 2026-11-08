# Operations runbook

All examples use the production Compose project:

```bash
export COMPOSE_FILE=compose.production.yml
export COMPOSE_ENV_FILES=.env.production
```

## Health and status

```bash
docker compose ps
curl --fail https://$APP_DOMAIN/health/live
curl --fail https://$APP_DOMAIN/health/ready
```

Liveness proves that the API process can respond. Readiness reports Redis as
`ok` or `degraded`; cache failure is intentionally degradable, so readiness
remains HTTP 200 while provider-backed requests can still run.

Only `edge` publishes host ports. `web`, `api`, and `redis` must show healthy
without published host bindings.

## Logs and request correlation

```bash
docker compose logs --since 15m edge api
docker compose logs --follow --tail 100 api
```

Caddy and application logs are JSON. Start an investigation with the
`X-Request-ID` returned to the client, then search the API logs for the same ID.
Never add Redis secrets, provider payloads, coordinates, or search queries to
diagnostic output.

## Internal metrics

The public edge returns 404 for `/metrics`. Inspect it from the API container or
attach an approved metrics collector to the private network:

```bash
docker compose exec -T api python -c \
  "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/metrics').read().decode())"
```

Monitor HTTP error rate and p95 latency, provider outcomes/latency, cache
miss/error rates, container restarts, disk capacity, Redis memory, and certificate
renewal. Alert thresholds must be calibrated on the selected host and traffic;
the Phase 6 smoke threshold is a regression gate, not a production SLO.

## Redis persistence and recovery

Redis is a reconstructible cache, but AOF with `appendfsync everysec` reduces
cold-cache churn after restarts. The named `redis_data` volume is the only Redis
state. Set `REDIS_MAXMEMORY` below available host memory so persistence and
allocator overhead have headroom.

For a consistent optional backup:

1. Start an AOF rewrite:

   ```bash
   docker compose exec -T redis sh -c \
     'REDISCLI_AUTH="$(cat /run/secrets/redis_password)" redis-cli BGREWRITEAOF'
   ```
2. Wait for `aof_rewrite_in_progress:0` in `INFO persistence`.
3. Snapshot or back up the Docker volume using host-approved tooling.

Restore into a stopped stack, verify file ownership, start Redis, then verify
readiness. Because the data is a cache, discarding a damaged volume is acceptable
when provider rate limits and cold-start traffic have been considered.

## Secret rotation

1. Generate a new random Redis password into a temporary mode-0600 file.
2. Stop `api` and `redis` during the short maintenance window.
3. Replace `secrets/redis_password.txt` atomically on the host.
4. Recreate Redis and API with `docker compose up --detach --force-recreate
   redis api --wait`.
5. Verify readiness and delete any temporary secret material.

Changing the password while the existing Redis process is running creates a
credential mismatch; rotate through a coordinated recreate.

## Common incidents

| Symptom | Checks | Response |
| --- | --- | --- |
| Edge unhealthy | `docker compose logs edge`; DNS; ports 80/443; Caddy volumes | Restore reachability or roll back Caddy configuration |
| API unhealthy | `docker compose logs api`; secret readability; settings validation | Correct configuration, recreate API, or roll back image |
| Redis unhealthy | Redis logs; secret match; volume ownership/disk/memory | Restore secret/volume health or recreate the cache |
| Provider errors | Provider outcome metrics, circuit state symptoms, Open-Meteo status | Preserve bounded retries; allow stale fallback; do not bypass circuits |
| Elevated latency | HTTP/provider histograms, cache hit rate, CPU/memory, network | Reduce load, restore cache/provider health, then scale after measurement |
| Bad release | Health checks and request logs for the exact SHA | Roll back to the last healthy immutable tag |

## Scaling constraint

Phase 7 intentionally runs one API worker because metrics are process-local and
request coalescing is per process. Scale-out requires an approved load-balancing
and Prometheus multiprocess/aggregation design; do not add Uvicorn workers without
addressing those boundaries.
