# Deploy / rollback

Production deploys promote an immutable GHCR image digest that has already passed CI. Never deploy `latest` or rebuild between staging and production.

## Preconditions

- `PALVELUT_IMAGE=ghcr.io/strayforest/palvelut@sha256:<64 hex>` is the tested image digest.
- `PALVELUT_RELEASE=<40-char commit SHA>` is the source revision that produced that digest.
- Production secrets remain in the external environment file and are not copied into deploy state.
- Database changes in the release follow expand → backfill → switch → contract-later compatibility.

## Deploy

From the application directory, with the production environment loaded:

```sh
bash infra/scripts/deploy-production.sh deploy
```

The workflow pulls the exact digest, selects the inactive blue/green slot, runs forward migrations, starts the inactive web container, waits for `/palvelut/health/ready`, then gracefully reloads Nginx to the new loopback port. Only after the web switch does it start the matching worker, warm-stop the previous worker with a 60-second grace period, and force-recreate the single scheduler from the same image digest. The previous web slot stays running for application rollback.

A failed pull, migration, readiness check, Nginx validation or reload stops the rollout. Nginx configuration is restored if the candidate upstream fails validation.

## Rollback

For an application-only rollback to the previously recorded image:

```sh
bash infra/scripts/deploy-production.sh rollback
```

Rollback does **not** reverse database migrations. It starts and health-checks the previous application image against the current schema, switches Nginx back, drains/replaces the worker and recreates the singleton scheduler. If the previous image is not compatible with the current schema, stop and use the database restore/migration incident plan; do not attempt an automatic destructive downgrade.

## State and verification

Non-secret release state is stored under `/opt/palvelut/deploy-state/`: active slot, current image/release and one previous image/release. Verify after deploy/rollback:

```sh
curl --fail https://<production-host>/palvelut/health/ready
docker compose -f compose.production.yml ps
cat /opt/palvelut/deploy-state/active-slot
```

Record release SHA, image digest, switch time, readiness result and rollback result in operational evidence. Never record secrets, database contents or personal data.
