#!/usr/bin/env bash
set -euo pipefail

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-palvelut}"
COMPOSE=(docker compose --project-name "$COMPOSE_PROJECT_NAME")

cleanup() {
  "${COMPOSE[@]}" down -v --remove-orphans
}
trap cleanup EXIT

rm -rf playwright-report test-results
mkdir -p playwright-report test-results

"${COMPOSE[@]}" build web e2e
"${COMPOSE[@]}" up -d postgres valkey web nginx

ready=0
for _ in $(seq 1 30); do
  status="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/ || true)"
  case "$status" in
    2??|3??|404)
      ready=1
      break
      ;;
  esac
  sleep 2
done

if test "$ready" != "1"; then
  "${COMPOSE[@]}" logs --no-color web nginx
  exit 1
fi

"${COMPOSE[@]}" run --rm web python manage.py seed_demo
"${COMPOSE[@]}" run --rm web python manage.py shell -c '
from django.contrib.auth import get_user_model
from django.utils import timezone
from palvelut.apps.discovery.services import rebuild_provider_read_document
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProfileRevision
from palvelut.apps.publishing.services import ensure_provider_slug
provider = Provider.objects.get(legal_name="Synthetic Helsinki Accounting Oy")
user, _ = get_user_model().objects.get_or_create(username="synthetic-visual-reviewer")
revision, _ = ProfileRevision.objects.update_or_create(
    provider=provider,
    status=ProfileRevision.Status.APPROVED,
    defaults={"payload": {"display_name": provider.display_name, "about": "Synthetic local demo data. Not a real provider."}, "created_by": user, "reviewed_at": timezone.now()},
)
ensure_provider_slug(provider_id=provider.id)
rebuild_provider_read_document(provider_id=provider.id)

onboarding_provider = Provider.objects.get(legal_name="Synthetic Espoo Legal Specialist")
onboarding_provider.claim_status = Provider.ClaimStatus.APPROVED
onboarding_provider.save(update_fields=("claim_status", "updated_at"))
account, _ = get_user_model().objects.get_or_create(
    username="provider-e2e@example.test",
    defaults={"email": "provider-e2e@example.test", "is_active": True},
)
account.email = "provider-e2e@example.test"
account.is_active = True
account.set_password("provider-e2e-pass")
account.save()
ProviderMembership.objects.update_or_create(
    provider=onboarding_provider,
    account=account,
    defaults={"role": ProviderMembership.Role.OWNER, "is_active": True},
)
'
"${COMPOSE[@]}" run --rm e2e
