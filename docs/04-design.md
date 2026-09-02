# Design direction

## Character

Nordic, calm and factual: public-service clarity with marketplace warmth. Avoid Russian flags, loud gradients, fake scarcity, glossy `verified` shields and stock-photo hero sections.

## Tokens

| Role | Value |
|---|---|
| Canvas | `#F6F7F4` |
| Surface | `#FFFFFF` |
| Text | `#17211D` |
| Muted text | `#5E6A65` |
| Brand/action | `#12664F` |
| Action hover | `#0B4F3C` |
| Info | `#245AA5` |
| Warning | `#9A5B00` |
| Danger | `#B42318` |
| Border | `#DDE3DF` |

- Typography: self-hosted Inter subset with `system-ui` fallback; 16px minimum body.
- Radius: 12px controls, 16px cards; shadows only for elevation.
- Spacing: 4px base; main content max-width 1200px.
- Touch targets: at least 44×44px; visible focus rings; never encode status by color alone.

## Page composition

### Home

Compact header → single-value proposition → two-field search → priority categories → `How checks work` → provider CTA → latest active profiles. The search remains above the fold at 360×800.

### Results

Desktop: results plus compact filter rail; mobile: list plus filter sheet. Start with list view; map is deferred. Show result count and applied filters before cards.

### Profile

Identity/trust summary first, evidence and details second. Primary contact stays reachable with one thumb; destructive/report actions are visually quiet but accessible.

### Provider workspace

Status and next required action first. Use a progress checklist, autosaved drafts, field-level errors and a true public preview. Analytics show definitions, not vanity charts.

## Content rules

- Use plain language and concrete nouns.
- Distinguish `checked by Finrix`, `declared by provider`, and `not checked`.
- Show timestamps in the reader's locale and retain the absolute date.
- Do not claim `best`, `safe`, `trusted`, or `licensed` without exact evidence.
- Use real provider work images; preserve aspect ratio and disclose if illustrative.

## Responsive/accessibility checks

Required widths: 360, 390, 768, 1024, 1440. Support 200% zoom, keyboard-only use, reduced motion, screen-reader labels, RU/FI text expansion and error summaries. Target WCAG 2.2 AA.

## Visual acceptance

P2 PRs retain full-page screenshots for home, results, empty state, profile and provider CTA at 360, 768 and 1440px. Review against this document for hierarchy, token use, text expansion, focus/error states, image treatment and horizontal overflow. A fresh review session must approve the evidence; pixel-perfect snapshots are not a substitute for accessibility or responsive checks.
