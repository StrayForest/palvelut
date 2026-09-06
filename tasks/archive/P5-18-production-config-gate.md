# P5-18 — Production-config gate

Completed the next active P5 gate: the canonical CI path validates the Django application under production configuration and fails closed for unsafe staging/production settings.

## Verification

- No duplicate production-config implementation was added: `palvelut/settings.py` already rejects staging/production startup when debug is enabled, the secret key or allowed hosts are implicit, or the public base URL is not HTTPS.
- The canonical `Compose stack` already runs `python manage.py check --deploy --fail-level ERROR` with explicit production environment, debug disabled, an explicit secret, an explicit allowed host and an HTTPS `/palvelut` public base URL.
- Exact pre-archive head `5c725147e2a98594b4b68d7902c973ec6c88a29f` passed `Compose stack` run `34010546462`, so the production deploy check was green before this gate was removed from the active document.
- This archive-only documentation change intentionally triggers the canonical CI workflow again so the final documentation head is verified before merge.

## Deviations

None.
