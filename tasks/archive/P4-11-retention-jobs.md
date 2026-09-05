# P4-11 — Analytics retention jobs

Archived from `tasks/P4-trust.md` after exact-head verification.

## Completed

- Raw analytics events expire after 90 days.
- A Celery task deletes only events older than the retention cutoff.
- Celery Beat schedules the purge daily at 03:20.
- Focused tests cover the 90-day boundary and the daily schedule contract.

## Verification

Implementation/verification exact head `679a1c19c47afd3943398b70d1d492c49bb55948` passed Compose stack run `33976834769`. Verification PR #119 was merged as `2ef5f10447dd92d6ebd9cecdb01b3eda01c9a4a3`.
