# P2-03 — Discovery filters and typo-tolerant synonyms

Status: complete.

## Scope

Complete the next P2 build step only: category/city/language/service-mode filters, typo-tolerant category synonyms and honest empty-result alternatives.

## Completed

- Added combinable category, city, language and service-mode filtering to the public discovery search.
- Added typo-tolerant matching over localized category labels and synonyms while preserving exact matching first.
- Kept city and service-mode constraints on the same `ServiceArea` relation so separate provider areas cannot satisfy one combined filter incorrectly.
- Invalid explicit filters now produce an honest empty result instead of falling back to unrelated providers.
- Added progressive empty-state alternatives that remove one active constraint rather than silently broadening the result set.
- Added server-rendered filter controls and regression coverage for typo matching, combined filters, cross-area mode semantics and empty alternatives.

## Verification

Exact-head Compose CI `33901923228` passed all 24 steps for `b05e10a88cc98b0db3802aee8963f80bc1a86e17`, including lint/format, mypy, dependency audit, secret scan, frontend/application builds, migrations, non-browser tests, browser gate, retained Playwright evidence and disposable smoke.
