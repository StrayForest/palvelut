# P1-17 — Query-count limits

## Scope

Close only the remaining P1 gate requiring database query-count limits. Do not expand into admin permission tests, public browse, or provider self-service.

## Completed

- Added a regression budget for rebuilding an existing `ProviderReadDocument` from the approved revision.
- The test exercises the real transactional `rebuild_provider_read_document()` service against the database and fails if the operation exceeds 8 SQL queries, including transaction/savepoint traffic captured by Django.
- The budget covers the current P1 read-model write path without introducing future public browse behavior.

## Verification

- `palvelut/apps/discovery/tests.py::ProviderReadDocumentTests::test_rebuild_existing_document_stays_within_query_budget` enforces the bound.
- Canonical exact-head Compose stack CI must pass before merge.

## Remaining

The only active P1 gate is admin permission tests.
