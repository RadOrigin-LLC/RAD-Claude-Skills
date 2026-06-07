# Current Plan

## Objective

Ship M4: invoice PDF export. By end of M4, a user can open any invoice in the app, click "Export PDF", and receive a deterministically-rendered PDF with the workspace's branding.

## Why this matters

Customers need a sendable invoice document. The HTML view inside Ledgerline isn't shareable — PDF is the universal handoff format.

## Non-goals

- Not adding email-the-invoice — separate milestone (M5)
- Not building a PDF template editor — fixed branded template only

## Current milestone

M4: Invoice PDF export via Puppeteer

## Acceptance criteria

- [x] Invoice React template renders identically in browser preview and PDF output
- [x] PDF wrapper accepts an invoice ID and produces a byte stream
- [ ] Workspace logo and brand color are embedded per the workspace settings
- [ ] E2E Playwright test covers invoice → PDF → download
- [ ] PDF render under 2s for a 20-line invoice on the CI runner

## Validation commands

- `pnpm test lib/invoices/` — PDF renderer unit tests
- `pnpm test tests/e2e/invoice-pdf.spec.ts` — Playwright end-to-end
- `pnpm typecheck` — strict TS passes
- `pnpm lint` — biome lint passes

## Planned changes

- [x] `lib/invoices/pdf.ts` — Puppeteer wrapper
- [x] `templates/invoice.tsx` — invoice template
- [ ] `lib/workspaces/branding.ts` — load workspace logo/color
- [ ] `tests/e2e/invoice-pdf.spec.ts` — Playwright suite

## Open questions

- Should PDF rendering happen server-side (current plan) or in a serverless worker for cost?
- Cache rendered PDFs in object storage, or render-on-demand each time?

## Risks

- Risk: Puppeteer Chromium download size bloats the CI image
  - Mitigation: use puppeteer-core + pinned Chromium revision in CI
- Risk: workspace logos in unsupported formats break the renderer
  - Mitigation: enforce PNG/JPEG validation at upload, with fallback to text mark

## Stop conditions

Stop and ask for approval if:

- The PDF byte output API surface must change
- A new dependency beyond puppeteer-core must be added
- Workspace settings schema changes

## Notes for the next session

- Most likely next step: write the E2E Playwright test and wire workspace branding
- Files likely to change: `tests/e2e/invoice-pdf.spec.ts`, `lib/workspaces/branding.ts`
- What must remain true: invoice rendering deterministic across runs (no embedded timestamps in PDFs)
