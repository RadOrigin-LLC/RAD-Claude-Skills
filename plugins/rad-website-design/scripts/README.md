# rad-website-design — Validators

Pure-stdlib Python validators. **No dependencies.** No install step.

These run in **Phase 1** of the `web-design-reviewer` agent and produce `[STATIC]` (high-confidence regex/AST) or `[HEURISTIC]` (pattern-likely-but-needs-verification) findings.

## Validators

### `check-viewport-meta.py`
Flags missing viewport meta, `user-scalable=no`, and `maximum-scale<5`. These are accessibility-sabotage anti-patterns (Tier 1, ADA lawsuit magnet).

```
python check-viewport-meta.py path/to/index.html
python check-viewport-meta.py --json src/
```

### `check-pure-bw.py`
Flags pure black (`#000`/`#000000`/`black`) and pure white (`#fff`/`#ffffff`/`white`) in CSS color/background declarations and Tailwind `bg-black`/`text-white` utilities. Causes halation/eye-strain (Tier 2).

```
python check-pure-bw.py styles/
python check-pure-bw.py --json src/
```

### `check-tap-targets.py`
Flags Tailwind interactive elements (`<button>`, `<a>`, `[role="button"]`, `onClick`) with `w-N h-N` or `size-N` below `w-11 h-11` (44×44px). WCAG / Apple / Android minimum. Mobile users 5× more likely to abandon on fat-finger errors.

```
python check-tap-targets.py src/components/
python check-tap-targets.py --json src/
```

## Honest scope

These validators are **regex-based static analysis**. They do NOT measure:
- Computed CSS sizes (verify with DevTools)
- Non-Tailwind sizing (CSS-driven — check Lighthouse or manually)
- Real contrast (use axe-core / Stark)
- Real Core Web Vitals (use Lighthouse / WebPageTest)

Each validator emits `--json` for programmatic consumption. Exit code 1 indicates findings; 0 indicates clean; 2 indicates target-not-found.

## Run all in parallel

```bash
TARGET=src/

python check-viewport-meta.py --json "$TARGET" > /tmp/viewport.json &
python check-pure-bw.py --json "$TARGET" > /tmp/bw.json &
python check-tap-targets.py --json "$TARGET" > /tmp/tap.json &
wait
```

The `web-design-reviewer` agent invokes them this way.
