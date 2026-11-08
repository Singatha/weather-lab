# Portable production deployment

## Scope

Phase 7 provides a production-like, single-host deployment that works on any
Linux machine with Docker Engine and Docker Compose. It does not create a cloud
account, DNS record, virtual machine, firewall, or managed service. Choose and
approve a hosting provider before automating infrastructure provisioning.

The production stack uses:

- Caddy as the only public service on TCP 80, TCP 443, and UDP 443
- an immutable Nginx image for the React application
- a single non-root FastAPI process on a private network
- authenticated Redis with AOF persistence and an `allkeys-lru` memory limit
- Docker secrets for the Redis password

The browser calls `/api/v1/*` on its own HTTPS origin. No runtime backend URL is
embedded in the production JavaScript bundle.

## Local production smoke test

Localhost uses Caddy's local certificate authority, so command-line smoke tests
need `--insecure` unless the local CA is trusted.

```bash
cp .env.production.example .env.production
mkdir -p secrets
umask 077
openssl rand -hex 32 > secrets/redis_password.txt

docker compose --env-file .env.production -f compose.production.yml \
  up --build --detach --wait
curl --fail --insecure https://localhost/
curl --fail --insecure https://localhost/health/live
```

Stop the stack without deleting Redis or Caddy data:

```bash
docker compose --env-file .env.production -f compose.production.yml down
```

Add `--volumes` only for an intentional full data reset.

## Internet host bootstrap

1. Provision a Linux host with current Docker Engine and the Compose plugin.
2. Point the domain's A/AAAA records to the host.
3. Permit inbound TCP 80, TCP 443, and UDP 443. Do not expose API port 8000 or
   Redis port 6379.
4. Clone this repository into the deployment directory.
5. Copy `.env.production.example` to `.env.production` and set:
   - `APP_DOMAIN` to the public hostname, such as `weather.example.com`
   - `PUBLIC_ORIGIN` to the matching `https://` origin
   - `IMAGE_PREFIX` to `ghcr.io/<owner>/<repository>` when using published images
   - `IMAGE_TAG` to an exact release version or commit SHA
6. Generate `secrets/redis_password.txt` with mode `0600` and a random value.
7. Authenticate the host to GHCR if the packages are private.
8. Start the exact published images:

   ```bash
   docker compose --env-file .env.production -f compose.production.yml \
     up --detach --no-build --wait
   ```

Caddy obtains and renews the public certificate when DNS resolves to the host,
ports 80/443 are reachable, and its `/data` volume persists. The edge redirects
HTTP to HTTPS automatically. `/metrics`, API docs, Redis, and origin containers
are not exposed publicly.

## Image release workflow

`.github/workflows/release.yml` runs for published GitHub releases and manual
dispatches. It builds the `production` target for API and web, publishes both to
GHCR with the immutable commit SHA plus applicable semantic-version tags, uses
BuildKit caches, and emits artifact attestations.

Manual dispatch has an optional `deploy` switch. The deploy job is deliberately
provider-neutral and requires a pre-provisioned host plus a protected GitHub
`production` environment.

Configure these GitHub environment values:

| Name | Kind | Purpose |
| --- | --- | --- |
| `DEPLOY_HOST` | secret | SSH hostname or address |
| `DEPLOY_USER` | secret | Restricted deployment account |
| `DEPLOY_SSH_PRIVATE_KEY` | secret | Dedicated SSH private key |
| `DEPLOY_KNOWN_HOSTS` | secret | Pinned host-key line; never disable checking |
| `DEPLOY_PATH` | variable | Absolute repository path on the host |

The host retains `.env.production`, the Redis secret, and registry credentials;
the workflow never copies those values from the repository.

## Rollback

Every deployment uses an exact image tag. To roll back, choose the last healthy
SHA or semantic version and run:

```bash
IMAGE_TAG=<previous-tag> docker compose --env-file .env.production \
  -f compose.production.yml pull api web
IMAGE_TAG=<previous-tag> docker compose --env-file .env.production \
  -f compose.production.yml up --detach --no-build --wait
```

Verify `/`, `/health/live`, and `/health/ready` after activation. Application
containers are stateless; rollback does not modify the Redis volume.
