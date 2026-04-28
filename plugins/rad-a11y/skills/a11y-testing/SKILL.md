---
name: a11y-testing
description: >
  Use this skill when the user asks about accessibility testing, axe-core, jest-axe, "@testing-library",
  "@axe-core/playwright", "Playwright accessibility testing", "WAVE", "Lighthouse accessibility",
  "automated a11y tests", "accessibility CI/CD", "eslint-plugin-jsx-a11y", "a11y linting",
  "axe DevTools", setting up accessibility tests, writing accessibility tests for React components,
  integrating a11y checks into a test suite, or understanding what automated tools can and cannot
  catch. Also use when asked to add automated a11y testing to a project.
---

# Accessibility Testing (real axe in your project)

This skill helps you set up **real accessibility testing** — eslint-plugin-jsx-a11y at write-time, jest-axe for components, @axe-core/playwright for e2e. Unlike `a11y-review` (which is static source analysis inside this plugin), this skill installs and configures the actual axe engine in *your* project so it runs against real rendered DOM.

Automated accessibility testing catches the well-known "low-hanging fruit" — roughly 30–80% of WCAG issues, depending on the page and the tooling. It is necessary but not sufficient. Always pair it with manual keyboard testing and real screen reader testing.

**Real axe (this skill's setup) catches:**
- Missing alt text (presence)
- Missing form labels and broken associations
- Duplicate IDs in rendered DOM
- Invalid ARIA attribute values against resolved roles
- Many contrast failures (when both colors are computed and resolvable at runtime)
- Empty button names / missing accessible names
- Some keyboard accessibility failures

**Real axe does NOT catch — requires manual testing:**
- Whether alt text is *meaningful* (not just present)
- Reading order matches visual order
- Live region announcement timing
- Keyboard interaction feel (does Tab order *make sense*?)
- Screen reader announcement coherence
- Custom widget keyboard contracts implemented end-to-end against the WAI-ARIA APG spec

**Real axe also misses some things `a11y-review` catches** — like Tailwind `outline-none` written without `focus-visible:ring-*` (axe sees the resolved `:focus` style; the source-pattern bug is invisible to it), and hardcoded ARIA state literals in JSX. Use both.

---

## The Testing Stack

| Layer | Tool | When |
|-------|------|------|
| Editor linting | `eslint-plugin-jsx-a11y` | As you type |
| Unit / component | `jest-axe` + `@testing-library/react` | Per component |
| E2E / integration | `@axe-core/playwright` | Per page flow |
| Manual browser audit | `axe DevTools` extension | During dev |
| CI gate | Playwright + axe in GitHub Actions | On every PR |

---

## eslint-plugin-jsx-a11y (Linting)

Catch accessibility violations at write-time, before any tests run.

```bash
npm install --save-dev eslint-plugin-jsx-a11y
```

```json
// .eslintrc.json
{
  "plugins": ["jsx-a11y"],
  "extends": ["plugin:jsx-a11y/recommended"]
}
```

**What it catches:**
- Missing `alt` on `<img>`
- Non-interactive elements with click handlers (`<div onClick>`)
- Missing ARIA roles for interactive patterns
- Invalid ARIA attribute values
- Missing `<label>` for inputs
- `autoFocus` on elements
- `href="#"` as a button substitute

**Recommended rules to add beyond "recommended":**
```json
{
  "rules": {
    "jsx-a11y/anchor-is-valid": "error",
    "jsx-a11y/no-autofocus": "warn",
    "jsx-a11y/interactive-supports-focus": "error",
    "jsx-a11y/label-has-associated-control": ["error", {
      "assert": "either"
    }]
  }
}
```

---

## jest-axe (Unit / Component Testing)

Test individual React components for accessibility violations.

```bash
npm install --save-dev jest-axe @testing-library/react @testing-library/jest-dom
```

### Basic Setup

```ts
// jest.setup.ts (or jest.setup.js)
import { toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);
```

```json
// jest.config.json
{
  "setupFilesAfterEnv": ["<rootDir>/jest.setup.ts"]
}
```

### Writing Component Tests

```tsx
// LoginForm.test.tsx
import { render } from '@testing-library/react';
import { axe } from 'jest-axe';
import LoginForm from './LoginForm';

describe('LoginForm accessibility', () => {
  it('has no axe violations in default state', async () => {
    const { container } = render(<LoginForm />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('has no axe violations when showing errors', async () => {
    const { container, getByRole } = render(<LoginForm />);

    // Trigger error state
    fireEvent.click(getByRole('button', { name: /sign in/i }));
    await waitFor(() => {
      expect(getByRole('alert')).toBeInTheDocument();
    });

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

### Testing Dynamic States

Always test all meaningful UI states — axe only scans the current DOM:

```tsx
// Test open dropdown
it('has no violations when dropdown is open', async () => {
  const { container, getByRole } = render(<Select options={options} />);

  // Open the dropdown
  fireEvent.click(getByRole('combobox'));

  const results = await axe(container);
  expect(results).toHaveNoViolations();
});

// Test modal open state
it('has no violations when modal is open', async () => {
  const { container, getByRole } = render(<ConfirmDialog isOpen={true} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Scoping and Rule Configuration

```tsx
// Scan only a specific component subtree
const results = await axe(container, {
  include: [['#payment-form']],
});

// Exclude a known-broken third-party widget
const results = await axe(container, {
  exclude: [['.third-party-widget']],
});

// Run only WCAG 2.1 AA rules
const results = await axe(container, {
  runOnly: {
    type: 'tag',
    values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'],
  },
});

// Disable a specific rule temporarily
const results = await axe(container, {
  rules: {
    'color-contrast': { enabled: false },  // requires visual verification
  },
});
```

---

## @axe-core/playwright (E2E Testing)

```bash
npm install --save-dev @axe-core/playwright
```

### Basic Page Scan

```ts
// tests/a11y.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Home page accessibility', () => {
  test('has no WCAG AA violations', async ({ page }) => {
    await page.goto('/');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(results.violations).toEqual([]);
  });
});
```

### Testing Interactive States

```ts
test('modal has no violations when open', async ({ page }) => {
  await page.goto('/dashboard');

  // Open the modal first
  await page.getByRole('button', { name: 'Add item' }).click();
  await page.getByRole('dialog').waitFor();

  // Now scan — only the current state is evaluated
  const results = await new AxeBuilder({ page })
    .include('#dialog-container')
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
```

### Handling Known Violations (Avoid Silencing Too Much)

```ts
// Create a fingerprint instead of snapshot-testing the full violation object
// (HTML snippets make snapshots brittle)
test('has only known pre-existing violations', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page }).analyze();

  // Fingerprint: rule ID + target selector only
  const violations = results.violations.map(v => ({
    id: v.id,
    targets: v.nodes.map(n => n.target),
  }));

  expect(violations).toMatchSnapshot('homepage-a11y-violations.json');
});
```

### Playwright Fixture Pattern (DRY)

```ts
// fixtures/a11y.ts
import { test as baseTest } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

export const test = baseTest.extend<{ axe: AxeBuilder }>({
  axe: async ({ page }, use) => {
    await use(
      new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .disableRules(['color-contrast'])  // visual only — always verify manually
    );
  },
});

export { expect } from '@playwright/test';
```

```ts
// tests/checkout.spec.ts
import { test, expect } from '../fixtures/a11y';

test('checkout flow is accessible', async ({ page, axe }) => {
  await page.goto('/checkout');
  expect((await axe.analyze()).violations).toEqual([]);

  await page.getByRole('button', { name: 'Continue to shipping' }).click();
  expect((await axe.analyze()).violations).toEqual([]);
});
```

### Attaching Reports in CI

```ts
test('full page scan', async ({ page }, testInfo) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page }).analyze();

  // Attach full results as artifact for debugging
  await testInfo.attach('accessibility-scan-results', {
    body: JSON.stringify(results, null, 2),
    contentType: 'application/json',
  });

  expect(results.violations).toEqual([]);
});
```

---

## GitHub Actions CI/CD Integration

```yaml
# .github/workflows/a11y.yml
name: Accessibility Tests

on: [push, pull_request]

jobs:
  a11y:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium

      - name: Build application
        run: npm run build

      - name: Start server
        run: npm start &
        env:
          PORT: 3000

      - name: Wait for server
        run: npx wait-on http://localhost:3000

      - name: Run accessibility tests
        run: npx playwright test tests/a11y/

      - name: Upload test artifacts
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: a11y-results
          path: playwright-report/
```

---

## axe-core Result Structure

Understanding results helps you write better assertions:

```ts
const results = await axe(container);
// or
const results = await new AxeBuilder({ page }).analyze();

results.violations  // ← Failed rules — MUST fix
results.passes      // ← Passed rules
results.incomplete  // ← "Needs review" — automated tool uncertain, requires manual check
results.inapplicable // ← Rules that had no applicable elements
```

### Violation Structure

```ts
results.violations.forEach(violation => {
  console.log(violation.id);          // Rule ID: "button-name", "label", etc.
  console.log(violation.impact);      // "critical" | "serious" | "moderate" | "minor"
  console.log(violation.description); // Human-readable description
  console.log(violation.helpUrl);     // Link to Deque documentation
  violation.nodes.forEach(node => {
    console.log(node.html);           // The offending HTML snippet
    console.log(node.target);         // CSS selector path to element
    node.any.forEach(check => {
      console.log(check.message);     // Specific failure message
    });
  });
});
```

### Key Rule IDs to Know

| Rule ID | WCAG | Description |
|---------|------|-------------|
| `button-name` | 4.1.2 | Button must have accessible name |
| `color-contrast` | 1.4.3 | Text contrast must be ≥ 4.5:1 |
| `image-alt` | 1.1.1 | Images must have alt text |
| `label` | 1.3.1 | Form inputs must have labels |
| `link-name` | 4.1.2 | Links must have accessible name |
| `landmark-one-main` | — | Page must have one main landmark |
| `region` | — | Content outside landmarks |
| `duplicate-id-active` | 4.1.1 | Focusable elements cannot share IDs |
| `aria-allowed-attr` | 4.1.2 | ARIA attrs must be valid for role |
| `aria-required-children` | 1.3.1 | Required child roles must be present |

---

## Manual Testing Protocol

Automated tools only catch ~30–80% of issues. Always supplement with:

### Keyboard-Only Navigation
1. Tab through entire page with mouse unplugged
2. Every element must show a visible focus indicator
3. Activate buttons/links with Enter and Space
4. Navigate complex widgets (menus, tabs) with arrow keys
5. Press Escape to close modals, menus, tooltips
6. Confirm focus returns to trigger after dismissal

### Screen Reader Smoke Test (15 minutes)
**NVDA + Chrome (Windows):**
- `Insert+F7` — list all headings, links, form elements
- `H` key — navigate by headings
- `B` key — navigate by buttons
- `F` key — navigate by form fields

**VoiceOver + Safari (macOS):**
- `VO+U` — rotor (headings, links, form controls)
- `VO+Right/Left` — navigate DOM order
- `VO+Cmd+H` — next heading

### Browser Extensions
- **axe DevTools** (Chrome/Firefox) — free, finds ~32% of issues automatically
- **WAVE** (Chrome/Firefox) — visual overlay, good for spot-checking
- **Colour Contrast Analyser** (standalone app) — precise contrast ratios

---

## What Automated Tools Miss

Flag these for mandatory manual verification:
- **Alt text quality** — tools verify it exists, not whether it's meaningful
- **Reading order** — DOM order vs visual order mismatch
- **Live region timing** — is the announcement happening at the right moment?
- **Focus indicator visibility** — technically present but too subtle?
- **Keyboard UX quality** — feels logical and efficient to use?
- **Screen reader announcement quality** — is the name/description actually useful?
- **Color-only meaning** — graphs, charts, status indicators
- **400% zoom reflow** — content accessible without horizontal scroll?
