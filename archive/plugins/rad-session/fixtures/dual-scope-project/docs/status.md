# Status

## Current state

- Branch / worktree: feat/invoice-pdf
- Current milestone: M4 — Invoice PDF export
- Overall status: on track

## Last completed

- Wired Puppeteer PDF rendering into `lib/invoices/pdf.ts`
- Implemented invoice-detail template at `templates/invoice.tsx`
- Added 12 unit tests for the PDF renderer (`lib/invoices/pdf.test.ts`)

## Files changed recently

- `lib/invoices/pdf.ts` — new file; Puppeteer PDF wrapper with deterministic font loading
- `templates/invoice.tsx` — new file; invoice-detail React template
- `lib/invoices/pdf.test.ts` — new file; 12 renderer tests
- `package.json` — added puppeteer-core ^22.0.0 (per approved candidate ADR 0003)

## Latest validation results

- Command: `pnpm test lib/invoices/` → pass (12/12)
- Command: `pnpm typecheck` → pass
- Command: `pnpm lint` → pass
- Command: `pnpm test tests/e2e/invoice-pdf.spec.ts` → not-run (Playwright suite pending CI runner setup)

## Decisions made during execution

- ADR 0003 (drafted): adopt puppeteer-core for invoice PDF rendering. Status: drafted but not yet committed.

## Known issues or blockers

No blockers this session.

## Next recommended step

Write the E2E Playwright test for invoice → PDF → download flow. First read `docs/planning/current.md` acceptance criterion 4. First question: should the CI runner install Chromium per-job or cache it?

## If restarting from scratch

- Read `AGENTS.md`
- Read `docs/planning/current.md`
- Resume with: "Write Playwright E2E for invoice PDF download per M4 AC 4 — first decide CI Chromium caching strategy"
