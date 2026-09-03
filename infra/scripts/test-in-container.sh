#!/usr/bin/env bash
set -euo pipefail

cd /workspace

git config --global --add safe.directory /workspace

uv lock --check

ruff check --extend-per-file-ignores 'tests/*.py:E402' manage.py palvelut tests
ruff format --check manage.py palvelut tests

mypy --ignore-missing-imports --follow-imports=skip --check-untyped-defs manage.py palvelut

uv export --locked --no-dev --format requirements-txt --output-file /tmp/palvelut-requirements.txt
pip-audit --disable-pip -r /tmp/palvelut-requirements.txt

mapfile -t tracked_files < <(git ls-files | grep -Ev '^(uv\.lock|frontend/package-lock\.json)$')
detect-secrets scan \
  --exclude-lines 'local-only|bootstrap-only|test-only|ci-only|explicit-secret' \
  "${tracked_files[@]}" \
  > /tmp/detect-secrets.json
python - <<'PY'
import json
from pathlib import Path

report = json.loads(Path("/tmp/detect-secrets.json").read_text())
results = report.get("results", {})
if results:
    for path, findings in results.items():
        for finding in findings:
            print(f"{path}:{finding.get('line_number')}: {finding.get('type')}")
    raise SystemExit("detect-secrets found candidate credentials")
PY

python manage.py makemigrations --check --dry-run

PALVELUT_ENVIRONMENT=production \
DJANGO_DEBUG=0 \
DJANGO_SECRET_KEY=test-only-not-a-real-secret \
DJANGO_ALLOWED_HOSTS=ci.example.invalid \
PUBLIC_BASE_URL=https://ci.example.invalid/palvelut \
python manage.py check --deploy --fail-level ERROR

python -m unittest discover -s tests -p 'test_*.py' -v
