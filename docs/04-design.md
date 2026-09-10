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

Compact header → single-value proposition → two-field search → priority categories → `How checks work` → prominent `Разместить карточку` provider CTA → latest active profiles. The search remains above the fold at 360×800. Provider registration must be discoverable directly from the header and home without opening an ambiguous workspace first.

### Results

Desktop: results plus compact filter rail; mobile: list plus filter sheet. Start with list view; map is deferred. Show result count and applied filters before cards.

### Profile

Identity/trust summary first, evidence and details second. Primary contact stays reachable with one thumb; destructive/report actions are visually quiet but accessible.

### Provider acquisition and workspace

The public `Разместить карточку` CTA and provider information page must explain the sequence before account creation: register → verify email → prove provider ownership/control → complete private profile → submit for review → publish after approval. Registration/login pages must look like first-class product surfaces rather than framework defaults.

After sign-in, show the current ownership/profile state and the single next required action first. A new account with no provider membership must be able to start a private provider claim. Pending ownership review must be explicit and must not look published. The workspace uses a progress checklist, autosaved drafts, field-level errors and a true public preview. Analytics show definitions, not vanity charts.

All product/staff UI copy is Russian-only. Do not design a language switcher or reserve UI space for FI/EN locale controls. Provider spoken languages remain profile/filter data and are not UI localization.

## Content rules

- Use plain Russian language and concrete nouns.
- Distinguish facts checked by Finrix, facts declared by provider, and facts not checked.
- Show timestamps consistently and retain the absolute date.
- Do not claim `best`, `safe`, `trusted`, or `licensed` without exact evidence.
- Use real provider work images; preserve aspect ratio and disclose if illustrative.

## Responsive/accessibility checks

Required widths: 360, 390, 768, 1024, 1440. Support 200% zoom, keyboard-only use, reduced motion, screen-reader labels, Russian text expansion and error summaries. Target WCAG 2.2 AA.

## Visual acceptance

P2 PRs retain full-page screenshots for home, results, empty state, profile and provider CTA at 360, 768 and 1440px.

Before P6 recruitment starts, retain a fresh provider-acquisition evidence set at 360, 390, 768, 1024 and 1440px for: public provider CTA, provider information page, register/login, new-provider bootstrap or claim state, workspace, edit and preview. Review the actual PNG evidence against this document for hierarchy, token use, Russian copy, focus/error states, image treatment and horizontal overflow. A fresh review session must approve the evidence; pixel-perfect snapshots are not a substitute for accessibility or responsive checks.
