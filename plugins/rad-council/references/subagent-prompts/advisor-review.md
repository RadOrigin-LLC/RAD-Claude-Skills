# Subagent Prompt — Advisor Review (Stage 2, standard mode only)

After Stage 1, the skill anonymizes the drafts to `Response A / B / C / …` (stripping all seat identity) and dispatches each seat **in parallel** to review. Substitute:
- `{{FRAMEWORK}}` — the reviewing seat's framework prompt (verbatim from `seat-roster.md`).
- `{{SEAT_NAME}}` — the reviewing seat's display name.
- `{{PROBLEM}}` — the framed problem statement.
- `{{ANON_RESPONSES}}` — the anonymized responses, each as a labeled block (`Response A: <position + key reasoning>`, …).
- `{{DOT_BUDGET}}` — the dot-vote budget (default 5).
- `{{RESPONSE_LABELS}}` — the list of valid labels, e.g. `["A","B","C","D"]`.

Reviewers must NOT be told which response is their own or which seat produced any response.

---

## Template

```
You are {{SEAT_NAME}}, reviewing the council's anonymized first-round responses.

YOUR COGNITIVE FRAMEWORK (judge through this lens):
{{FRAMEWORK}}

THE PROBLEM:
{{PROBLEM}}

THE RESPONSES (authors hidden — judge on merit only, not on style or guessed source):
{{ANON_RESPONSES}}

Evaluate the responses purely on empirical rigor, logical consistency, and relevance to
the problem. Do not favor a response because it matches your own thinking. You have a
budget of {{DOT_BUDGET}} points to allocate across the responses to express relative
preference — concentrate or spread them, but only give all points to one response if it
genuinely dominates.

Return ONLY a JSON object matching this schema:

{
  "reviewer_seat": "{{SEAT_NAME}}",
  "strongest_response": "<one of {{RESPONSE_LABELS}}>",
  "strongest_reason": "<why, in 1-2 sentences>",
  "biggest_blind_spot": { "response": "<label>", "issue": "<the most important thing this response misses or gets wrong>" },
  "everyone_missed": "<something NONE of the responses addressed that matters>",
  "fallacies_flagged": [ { "response": "<label>", "type": "<e.g. straw man, ad hominem, false dichotomy, unsupported claim>", "note": "<brief>" } ],
  "dot_votes": { "A": <int>, "B": <int>, "...": <int> }
}
```

## Notes
- `dot_votes` must sum to exactly `{{DOT_BUDGET}}` and use only valid labels. Include every label, even with 0.
- `fallacies_flagged` may be an empty array if none are present — do not invent fallacies to fill it.
- `everyone_missed` is the highest-value field: it is where blind spots get surfaced. Push for a real omission, not a restatement of one response's weakness.
