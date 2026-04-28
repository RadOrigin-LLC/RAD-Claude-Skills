---
name: a11y-keyboard-focus
description: >
  Use this skill when the user asks about keyboard navigation, keyboard accessibility, focus
  management, focus trapping, focus ring, focus indicator, ":focus-visible", skip links,
  "tabindex", "Tab key navigation", "focus order", "focus returns", "orphaned focus",
  "focus lost", "modal focus trap", "focus after close", "roving tabindex", "keyboard trap",
  or is building modals, dialogs, drawers, dropdowns, or any component requiring programmatic
  focus management. Also use when diagnosing why keyboard navigation feels broken.
---

# Keyboard Navigation and Focus Management

> **Skill type: Reference.** This is teaching/pattern content — it explains keyboard contracts, focus management strategies, and focus-restoration patterns for modals/dialogs. It is not a scanner. Static review (`/a11y-review`) catches common keyboard/focus source patterns; *runtime keyboard feel* (Tab order making sense, focus indicator quality) requires browser testing.

Keyboard accessibility is non-negotiable for WCAG 2.1.1 (Keyboard) and required for motor-impaired users, power users, and assistive technology users. Every interactive element must be reachable and operable via keyboard alone.

---

## Focus Fundamentals

### What Receives Focus

By default, only natively focusable elements receive keyboard focus:
- `<a href="...">` — links with valid `href`
- `<button>`, `<input>`, `<select>`, `<textarea>` — form controls
- `<summary>` — disclosure toggle
- Elements with `tabindex="0"` — explicitly focusable
- Elements with `tabindex="-1"` — programmatically focusable only (not via Tab)

**`tabindex` values:**
| Value | Effect |
|-------|--------|
| `0` | Element enters natural Tab order at its DOM position |
| `-1` | Element is focusable via `element.focus()` but excluded from Tab order |
| `> 0` | **Never use.** Overrides natural order, causes confusing navigation |

### Tab Order = DOM Order

Focus follows the DOM order, not the visual layout. CSS reordering (`flex-direction: row-reverse`, `order`, `grid-template-areas`, `position: absolute`, `float`) creates a mismatch between what users see and where focus goes.

```html
<!-- Visual order: B A — Tab order: A B (DOM order) -->
<div style="display:flex; flex-direction:row-reverse">
  <button>A</button>  <!-- Tab focuses A first -->
  <button>B</button>  <!-- Then B — opposite of visual order -->
</div>
```

Always verify DOM order matches visual reading order.

---

## Focus Indicators (WCAG 2.4.7, 2.4.11)

### The Rule: Never Remove Without Replacing

```css
/* ❌ FORBIDDEN: Removes focus indicator for keyboard users */
* { outline: none; }
button:focus { outline: 0; }
.btn:focus { outline: none; }

/* ✅ CORRECT: Replace with high-visibility custom indicator */
button:focus-visible {
  outline: 3px solid #005fcc;
  outline-offset: 2px;
}
```

### `:focus` vs `:focus-visible`

- `:focus` — fires on every focus event, including mouse clicks (shows ring on clicked buttons)
- `:focus-visible` — fires only when the browser determines keyboard navigation is in use

```css
/* Remove default outline on click, keep it for keyboard navigation */
button:focus { outline: none; }
button:focus-visible {
  outline: 3px solid #005fcc;
  outline-offset: 2px;
  border-radius: 4px;
}
```

### Tailwind Focus Indicators

```html
<!-- ❌ WRONG: Removes focus ring with no replacement -->
<button class="outline-none">Submit</button>

<!-- ✅ CORRECT: Custom focus ring using focus-visible -->
<button class="focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 rounded">
  Submit
</button>
```

### Focus Indicator Requirements (WCAG 2.4.11 — new in 2.2)
- Must not be completely hidden by other content
- Must meet 3:1 contrast ratio against adjacent colors
- Minimum: enclose the component (not just a 1px underline)

### High-Contrast Focus Ring (recommended)

```css
/* Visible in both light and dark themes, plus high-contrast mode */
:focus-visible {
  outline: 3px solid;
  outline-offset: 3px;
  /* 'currentColor' inherits from the text color, maintaining contrast in any theme */
  outline-color: currentColor;
}
```

---

## Skip Links (WCAG 2.4.1)

Skip links let keyboard users bypass repetitive navigation to reach the main content directly.

```html
<!DOCTYPE html>
<html lang="en">
<head>...</head>
<body>

  <!-- Must be the FIRST focusable element -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <header>
    <nav aria-label="Primary">
      <!-- Long navigation with many links -->
    </nav>
  </header>

  <main id="main-content" tabindex="-1">
    <h1>Page Title</h1>
    <!-- Page content -->
  </main>

</body>
</html>
```

```css
/* Visually hidden by default, visible on focus */
.skip-link {
  position: absolute;
  left: -9999px;
  top: auto;
  width: 1px;
  height: 1px;
  overflow: hidden;
  z-index: -999;
}
.skip-link:focus {
  position: fixed;
  top: 0;
  left: 0;
  width: auto;
  height: auto;
  overflow: auto;
  z-index: 999;
  padding: 1rem;
  background: #000;
  color: #fff;
  font-size: 1.2rem;
  outline: 3px solid #fff;
}
```

**Tailwind implementation:**
```html
<a
  href="#main-content"
  class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-black focus:text-white focus:rounded"
>
  Skip to main content
</a>
```

**`tabindex="-1"` on `<main>`:** Required for the skip link to work correctly in all browsers. Without it, some browsers do not actually scroll to or focus the target when the link is activated.

---

## Modal and Dialog Focus Management (WCAG 2.1.2)

Modals require strict focus management to prevent users from interacting with background content.

### The 4 Rules of Modal Focus

1. **On open:** Move focus to the first interactive element inside the modal, or to the modal container itself if no interactive elements exist
2. **While open:** Trap `Tab` and `Shift+Tab` inside the modal
3. **On `Escape`:** Close the modal, return focus to the trigger
4. **On close (any method):** Return focus to the element that opened the modal

### React Modal Focus Management

```tsx
import { useEffect, useRef } from 'react';

function Modal({ isOpen, onClose, children }) {
  const modalRef = useRef(null);
  const triggerRef = useRef(null);

  // Store trigger reference on open
  useEffect(() => {
    if (isOpen) {
      triggerRef.current = document.activeElement;
      // Focus the modal container or first focusable element
      modalRef.current?.focus();
    } else {
      // Return focus to trigger on close
      triggerRef.current?.focus();
    }
  }, [isOpen]);

  // Trap focus within modal
  function handleKeyDown(e) {
    if (e.key === 'Escape') {
      onClose();
      return;
    }
    if (e.key !== 'Tab') return;

    const focusable = modalRef.current?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last  = focusable[focusable.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  if (!isOpen) return null;

  return (
    <div
      ref={modalRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      tabIndex={-1}
      onKeyDown={handleKeyDown}
      className="focus:outline-none"
    >
      {children}
    </div>
  );
}
```

### Background Inert Pattern (modern approach)

```html
<!-- The inert attribute handles both focus trapping AND aria-hidden -->
<main inert>...</main>
<nav inert>...</nav>

<div role="dialog" aria-modal="true">
  <!-- Only this receives focus -->
</div>
```

`inert` is now baseline (Chrome 102+, Firefox 112+, Safari 15.5+). For older browser support, polyfill or use the manual trap pattern above.

---

## Focus Drift — React-Specific

When React removes elements from the DOM, focus is "orphaned" and resets to `<body>`.

### Pattern: Return Focus After Deletion

```tsx
// User deletes a list item — focus must not be lost
function ItemList({ items, onDelete }) {
  const lastItemRef = useRef(null);
  const listRef = useRef(null);

  function handleDelete(index) {
    onDelete(index);

    // After deletion, focus previous item (or the list itself)
    requestAnimationFrame(() => {
      const remaining = listRef.current?.querySelectorAll('[data-item]');
      const target = remaining?.[Math.min(index, remaining.length - 1)];
      (target ?? listRef.current)?.focus();
    });
  }

  return (
    <ul ref={listRef}>
      {items.map((item, i) => (
        <li key={item.id} data-item>
          {item.name}
          <button onClick={() => handleDelete(i)}>Delete</button>
        </li>
      ))}
    </ul>
  );
}
```

### Pattern: Route Change Focus Management

On single-page app (SPA) navigation, focus resets to `<body>`. Move it to the page heading or `<main>`:

```tsx
// React Router / Next.js App Router pattern
useEffect(() => {
  const heading = document.querySelector('h1');
  heading?.setAttribute('tabindex', '-1');
  heading?.focus();
}, [pathname]);  // pathname from usePathname() or location
```

---

## Keyboard Patterns for Common Components

### Dropdown / Select Menu

| Key | Action |
|-----|--------|
| `Enter` / `Space` | Open menu |
| `↑` / `↓` | Navigate options |
| `Enter` | Select highlighted option |
| `Escape` | Close, return focus to trigger |
| `Home` / `End` | Jump to first/last option |
| `A–Z` | Type-ahead (jump to matching option) |

### Date Picker (Calendar Grid)

| Key | Action |
|-----|--------|
| `→` / `←` | Next/previous day |
| `↑` / `↓` | Same day, next/previous week |
| `Page Up` / `Page Down` | Previous/next month |
| `Home` / `End` | First/last day of week |
| `Enter` | Select date |
| `Escape` | Close picker |

### Carousel / Slider

| Key | Action |
|-----|--------|
| `→` / `←` | Next/previous slide |
| `Home` | First slide |
| `End` | Last slide |

Pause auto-rotation when focused. Provide pause/stop control.

### Tree View

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate items |
| `→` | Expand collapsed node; move to first child if expanded |
| `←` | Collapse expanded node; move to parent |
| `Enter` | Select / activate item |
| `Home` / `End` | First/last visible item |

---

## Common Keyboard Anti-Patterns

```html
<!-- ❌ TRAP: Dropdown with no Escape key handler -->
<div role="listbox" onkeydown="handleArrows(event)">
  <!-- User cannot exit! -->
</div>

<!-- ❌ TRAP: Modal that doesn't trap focus -->
<div role="dialog">
  <button>Action</button>
  <!-- Tab exits dialog to background content -->
</div>

<!-- ❌ USELESS CUSTOM BUTTON: No keyboard activation -->
<div
  role="button"
  tabindex="0"
  onclick="doAction()"
  <!-- Missing: onkeydown for Enter and Space -->
>
  Click me
</div>

<!-- ❌ POSITIVE TABINDEX: Breaks natural order -->
<button tabindex="3">First visually</button>
<button tabindex="1">Gets focus first</button>  <!-- Confusing! -->
<button tabindex="2">Gets focus second</button>
```

---

## Testing Keyboard Accessibility

**Manual test procedure:**
1. Disconnect your mouse
2. `Tab` through the entire page — every interactive element should receive visible focus
3. Verify reading order matches visual order
4. Activate every control with `Enter` and `Space`
5. Open modals/menus — verify focus moves in, `Escape` closes and returns focus
6. Delete/toggle items — verify focus doesn't go to `<body>`
7. Attempt to Tab out of any open modal — focus should stay inside

**Screen readers to test:**
- NVDA + Chrome (Windows, free)
- VoiceOver + Safari (macOS/iOS, built-in)
- JAWS + Chrome or Edge (Windows, industry standard)
