---
name: a11y-forms
description: >
  Use this skill when the user asks about accessible forms, form labels, form errors, input
  accessibility, "aria-required", "aria-invalid", "aria-describedby", fieldset and legend,
  "form validation accessibility", required fields, error messages, placeholder accessibility,
  password fields, file uploads, date inputs, select elements, checkbox groups, radio groups,
  "WCAG 3.3", "label instructions", or is building any form that needs to be screen reader
  compatible and keyboard accessible.
---

# Form Accessibility

> **Skill type: Reference.** This is teaching/pattern content — it explains label association, error announcement, fieldset/legend grouping, and validation patterns. It is not a scanner. For static review of existing forms, use `/a11y-review`. For runtime verification of error announcements and validation behavior, set up real axe via the `a11y-testing` skill and pair with manual screen reader testing.

Forms are the most interaction-critical UI element — and the most commonly broken for assistive technology users. Missing labels, inaccessible errors, and placeholder-as-label are among the top WCAG failures on the web.

---

## The Non-Negotiable Rules

1. **Every input must have a visible, programmatically associated label.** No exceptions.
2. **Never use `placeholder` as a label.** Placeholder disappears on input, fails contrast, and is not reliably announced by screen readers.
3. **Errors must be text, linked to the input, and not rely on color alone.**
4. **Required fields must be indicated programmatically** (`required` or `aria-required="true"`).

---

## Label Association

### Method 1: Explicit Association (Preferred)

```html
<label for="email">Email Address</label>
<input type="email" id="email" name="email" autocomplete="email">
```

In React (`htmlFor` instead of `for`):
```tsx
<label htmlFor="email">Email Address</label>
<input type="email" id="email" name="email" autoComplete="email" />
```

### Method 2: Wrapping Label

```html
<label>
  Email Address
  <input type="email" name="email">
</label>
```

Works well for radio/checkbox where the label and input are adjacent.

### Method 3: aria-label (No Visible Label)

Use only when a visible label is genuinely not possible (e.g., search bar with a button):
```html
<form role="search">
  <input type="search" aria-label="Search products" name="q">
  <button type="submit">
    <svg aria-hidden="true">...</svg>
    <span class="sr-only">Search</span>
  </button>
</form>
```

### Method 4: aria-labelledby (From Existing Text)

```html
<h2 id="billing-title">Billing Address</h2>
<div role="group" aria-labelledby="billing-title">
  <label for="street">Street</label>
  <input id="street" type="text">
</div>
```

---

## Placeholder — What It's For (Not Labels)

```html
<!-- ❌ WRONG: Placeholder as the only label — disappears on typing -->
<input type="email" placeholder="Enter your email address">

<!-- ✅ CORRECT: Label + optional placeholder as a hint -->
<label for="email">Email Address</label>
<input
  type="email"
  id="email"
  placeholder="name@company.com"
  autocomplete="email"
>
```

Placeholder text must meet 4.5:1 contrast ratio if it conveys meaning — most design systems use `text-gray-400` which typically fails.

---

## Required Fields (WCAG 3.3.2)

```html
<!-- Method 1: HTML required attribute (simplest, preferred) -->
<label for="name">
  Full Name
  <span aria-hidden="true">*</span>  <!-- Visual asterisk, hidden from AT -->
</label>
<input type="text" id="name" required>

<!-- Method 2: aria-required (when not using native validation) -->
<input type="text" id="name" aria-required="true">

<!-- Include a form-level note explaining the asterisk -->
<p id="required-note">Fields marked with <span aria-hidden="true">*</span>
  <span class="sr-only">an asterisk</span> are required.
</p>
```

Never indicate required status by color alone (red label text) — fails WCAG 1.4.1.

---

## Error Messages (WCAG 3.3.1)

### The Pattern: aria-describedby + aria-invalid

```html
<label for="email">Email Address *</label>
<input
  type="email"
  id="email"
  name="email"
  required
  aria-required="true"
  aria-invalid="true"
  aria-describedby="email-error email-hint"
  class="border-red-500"
>

<!-- Error message: linked via aria-describedby -->
<p id="email-error" class="text-red-600 text-sm mt-1" role="alert">
  <!-- role="alert" announces immediately when injected -->
  Please enter a valid email address.
</p>

<!-- Optional hint: also linked via aria-describedby -->
<p id="email-hint" class="text-gray-500 text-xs mt-1">
  We'll send your receipt here.
</p>
```

**Rules:**
- `aria-invalid="true"` — set when field has an error; removes it on correction
- `aria-describedby` can reference multiple IDs (space-separated, read in order)
- Error text must be visible, not just announced
- Use `role="alert"` on the error container to announce immediately when injected
- Never rely on color (red border) as the only error indicator

### React Form Error Pattern

```tsx
function EmailInput() {
  const [value, setValue] = useState('');
  const [error, setError] = useState('');

  function validate(val) {
    if (!val) return 'Email is required.';
    if (!val.includes('@')) return 'Enter a valid email address.';
    return '';
  }

  function handleBlur() {
    setError(validate(value));
  }

  const hasError = !!error;

  return (
    <div>
      <label htmlFor="email">
        Email Address <span aria-hidden="true">*</span>
      </label>
      <input
        id="email"
        type="email"
        value={value}
        onChange={e => setValue(e.target.value)}
        onBlur={handleBlur}
        required
        aria-required="true"
        aria-invalid={hasError}
        aria-describedby={hasError ? 'email-error' : undefined}
      />
      {hasError && (
        <p id="email-error" role="alert" className="text-red-600 text-sm">
          {error}
        </p>
      )}
    </div>
  );
}
```

### Error Summary for Multi-Field Forms

When a form has multiple errors, inject a summary at the top and move focus to it:

```html
<div
  id="error-summary"
  role="alert"
  aria-labelledby="error-title"
  tabindex="-1"
>
  <h2 id="error-title">3 errors prevent submission</h2>
  <ul>
    <li><a href="#email">Email: Please enter a valid email address</a></li>
    <li><a href="#phone">Phone: Phone number is required</a></li>
    <li><a href="#postal">Postal Code: Invalid format</a></li>
  </ul>
</div>
```

```js
// On submit with errors, inject summary then focus it
errorSummaryEl.focus();
```

---

## Fieldset and Legend (WCAG 1.3.1)

Group related inputs — especially radio buttons and checkboxes — in `<fieldset>` with `<legend>`:

```html
<!-- Radio group -->
<fieldset>
  <legend>Preferred Contact Method</legend>

  <label>
    <input type="radio" name="contact" value="email"> Email
  </label>
  <label>
    <input type="radio" name="contact" value="phone"> Phone
  </label>
  <label>
    <input type="radio" name="contact" value="sms"> SMS
  </label>
</fieldset>

<!-- Checkbox group -->
<fieldset>
  <legend>Notification Preferences <span aria-hidden="true">*</span></legend>
  <p id="notifications-hint" class="text-sm text-gray-500">
    Select at least one notification type.
  </p>

  <label>
    <input type="checkbox" name="notify" value="email" aria-describedby="notifications-hint">
    Email notifications
  </label>
  <label>
    <input type="checkbox" name="notify" value="sms" aria-describedby="notifications-hint">
    SMS notifications
  </label>
</fieldset>
```

Screen readers announce the legend text before each option in the group: "Preferred Contact Method, Email, radio button, 1 of 3."

---

## Select Elements

```html
<!-- Standard select -->
<label for="country">Country</label>
<select id="country" name="country" autocomplete="country">
  <option value="">Select a country</option>
  <option value="us">United States</option>
  <option value="ca">Canada</option>
</select>

<!-- Select with groups -->
<label for="timezone">Timezone</label>
<select id="timezone" name="timezone">
  <optgroup label="Americas">
    <option value="america/new_york">Eastern Time (UTC−5)</option>
    <option value="america/chicago">Central Time (UTC−6)</option>
  </optgroup>
  <optgroup label="Europe">
    <option value="europe/london">London (UTC+0)</option>
  </optgroup>
</select>
```

Native `<select>` is fully accessible. Prefer it over custom dropdown widgets. If you must build a custom combobox, follow the ARIA combobox pattern (see a11y-aria-patterns skill).

---

## Input Types and Autocomplete

Use the correct `type` attribute — it provides the right virtual keyboard on mobile and AT context:

| Type | Use For |
|------|---------|
| `type="email"` | Email addresses |
| `type="tel"` | Phone numbers |
| `type="url"` | URLs |
| `type="number"` | Numeric values |
| `type="password"` | Passwords (masked) |
| `type="search"` | Search fields |
| `type="date"` | Date selection |

Always add `autocomplete` attributes — they help users with cognitive disabilities and motor impairments:

```html
<input type="text"     id="name"    autocomplete="name">
<input type="email"    id="email"   autocomplete="email">
<input type="tel"      id="phone"   autocomplete="tel">
<input type="text"     id="address" autocomplete="street-address">
<input type="password" id="pw"      autocomplete="current-password">
<input type="password" id="new-pw"  autocomplete="new-password">
```

WCAG 1.3.5 (AA) requires `autocomplete` on inputs collecting personal information.

---

## File Uploads

```html
<label for="avatar">Profile Photo (optional)</label>
<input
  type="file"
  id="avatar"
  name="avatar"
  accept="image/png, image/jpeg"
  aria-describedby="avatar-hint"
>
<p id="avatar-hint" class="text-sm text-gray-500">
  PNG or JPEG, maximum 2MB.
</p>
```

Custom file upload buttons — hide the native input visually but keep it accessible:
```html
<label for="file-upload" class="cursor-pointer btn">
  Choose File
  <input
    type="file"
    id="file-upload"
    class="sr-only"  {/* Visually hidden but accessible */}
  >
</label>
```

---

## Password Fields

```html
<label for="password">Password</label>
<div class="relative">
  <input
    type="password"
    id="password"
    autocomplete="current-password"
    aria-describedby="password-strength"
  >
  <button
    type="button"
    aria-label="Show password"
    aria-pressed="false"
    onclick="togglePassword(this)"
  >
    <svg aria-hidden="true"><!-- eye icon --></svg>
  </button>
</div>
<div id="password-strength" aria-live="polite" class="sr-only">
  <!-- Announce strength changes: "Password strength: strong" -->
</div>
```

WCAG 2.2 Accessible Authentication (3.3.8): Do not prevent paste in password fields. Allow password managers.

---

## Form Submission Feedback

### Success
```html
<!-- Move focus to confirmation message after successful submission -->
<div
  id="success-msg"
  role="status"
  aria-live="polite"
  tabindex="-1"
  class="p-4 bg-green-50 rounded"
>
  <h2>Order placed successfully!</h2>
  <p>Confirmation #12345 sent to your email.</p>
</div>
<!-- JS: document.getElementById('success-msg').focus() -->
```

### Submitting State
```html
<button type="submit" aria-disabled="true" aria-busy="true">
  <span aria-hidden="true">
    <!-- spinner SVG -->
  </span>
  Submitting...
</button>
```

Use `aria-busy="true"` during async submission. Use `aria-disabled` (not `disabled`) if you want the button to remain focusable while processing.

---

## Common Form Anti-Patterns

```html
<!-- ❌ Placeholder-only label -->
<input placeholder="Email address">

<!-- ❌ Label not linked to input -->
<label>Email</label>
<input type="email" name="email">
<!-- No for/id match — screen reader cannot connect them -->

<!-- ❌ Error with color only -->
<input class="border-red-500">
<!-- No text error, no aria-invalid, no aria-describedby -->

<!-- ❌ Required indicated only visually -->
<label class="text-red-600">Email</label>
<!-- No required or aria-required attribute on the input -->

<!-- ❌ Radio group without fieldset/legend -->
<div>
  <p>Preferred contact method</p>  <!-- Screen reader never reads this with each radio -->
  <label><input type="radio" name="contact"> Email</label>
  <label><input type="radio" name="contact"> Phone</label>
</div>
```
