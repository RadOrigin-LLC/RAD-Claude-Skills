# Conversion & Microcopy — 2026 Reference

## Microcopy principles

1. **Active verbs.** "Start free trial" beats "Sign up." "Save and continue" beats "Submit."
2. **Benefit-driven.** "Sync your data — almost there!" beats "Processing data synchronization."
3. **Plain language.** Reading level grade 6–8. No jargon outside specialist tools.
4. **Reduce decision friction at the action.** Trust markers and reassurance copy adjacent to commitment buttons.

## CTA wording

| Bad | Good | Why |
|---|---|---|
| Submit | Save and continue | Specific verb |
| Click here | Open dashboard | Action + object |
| Pioneering Tomorrow | Start free trial | Function over poetry |
| Get Started | Get my report | Personal pronoun |
| Sign up | Create your account (free) | Reassurance in copy |
| Buy Now | Add to cart | Lower commitment first |

## Form microcopy

- **Field labels:** action-oriented ("Email address" not "Email")
- **Helper text:** explain WHY when ambiguous ("Used only for receipt — never shared")
- **Inline validation:** real-time, on blur, with the specific fix:
  - Bad: "Invalid input"
  - Good: "Email needs an @ symbol — e.g. you@example.com"
- **Required vs. optional:** label what's optional, not what's required, when most fields are required: `Phone (optional)`

## Trust signals near commitment

Place trust markers and risk-reversal copy directly adjacent to the action button — not in the footer.

```html
<button class="cta-primary">Start free trial</button>
<p class="trust-strip">
  No credit card required · Cancel anytime · 14-day full access
</p>
```

## Risk reversal copy patterns

- **No commitment:** "No credit card required"
- **Reversibility:** "Cancel anytime in one click"
- **Money back:** "60-day refund, no questions asked"
- **Privacy:** "We never share your email"
- **Free pricing:** "Free forever for personal use"

Adjacent placement matters — far-from-CTA disclaimers don't reduce friction.

## Above-the-fold trust signals

- Star aggregate (4.5+/5 with review count)
- "Trusted by 50,000+ teams"
- Logo wall (3–5 recognizable customer logos)
- SOC 2 / GDPR / SSL badge if relevant

Generic "We're trusted" claims without numbers read as fake.

## Testimonial structure

Every testimonial needs:
- Real name
- Real role
- Real photo
- **Specific outcome with numbers** ("Cut our processing time from 6 hours to 8 minutes")

Testimonials without specifics ("Great product!") are damaging — they signal stock photos.

## Empty state copy

```
[Illustration]
No invoices yet.
Send your first invoice in under 30 seconds.

[Button] Create invoice
[Link] See sample invoices
```

Educational + branded + clear next action. Never "No data" alone.

## Error message templates

```
[Icon] We couldn't process your card.
- Card was declined by your bank.
- Try another card or contact your bank.

[Button] Update payment
[Link] Contact support
```

Pattern: **what happened** → **why** → **fix**. Always paired with icon + text (not color alone).

## Loading state copy

- <1s: no copy needed
- 1–3s: spinner + nothing or "Loading..."
- 3–10s: progress bar + "Processing your data..."
- 10s+: progress bar + step indicator + "This usually takes about 30 seconds. Almost there!"

Fake progress is acceptable for the 1–3s range; **don't fake** longer durations — users feel the lie.

## Onboarding microcopy

Cap at 3–5 steps. Each step:
- Shows progress (`Step 2 of 4`)
- Has an actionable button (no passive "Next")
- Explains the value of the step in one line

```
Step 2 of 4 — Connect your data source

[Connect Postgres] · [Connect MongoDB] · [Skip — I'll do this later]

Why now? Connecting your DB lets you query in plain English on the next screen.
```

## Anti-patterns (cross-ref)

- Vague microcopy / jargon → SHOULD-AVOID #15
- Confirm-shaming ("No thanks, I hate saving money") → AVOID-AT-ALL-COSTS #4
- Generic praise testimonials → SHOULD-AVOID

## A/B test priority

If you can only test a few microcopy changes, prioritize:
1. Primary CTA button text
2. Form submit button text
3. Pricing page tagline
4. Empty-state primary action
5. First-paragraph above the fold
