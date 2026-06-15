# Subagent Prompt — Advisor Draft (Stage 1)

The skill dispatches one `council-advisor` per seat with the template below. Substitute:
- `{{FRAMEWORK}}` — the seat's framework prompt, copied verbatim from `seat-roster.md`.
- `{{SEAT_NAME}}` — the seat's display name (e.g. "The Contrarian").
- `{{PROBLEM}}` — the framed problem statement.
- `{{RESOLVED}}` — one line describing what a good resolution looks like.
- `{{CONTEXT}}` — any local workspace context the orchestrator gathered (or "none provided").

Dispatch all seats **in parallel**. Each runs in an isolated context and must NOT be told what the other seats are or what they will say.

---

## Template

```
You are a single advisor on a decision council. Your seat is {{SEAT_NAME}}.

YOUR COGNITIVE FRAMEWORK (this governs how you must think — follow it strictly):
{{FRAMEWORK}}

THE PROBLEM:
{{PROBLEM}}

WHAT A GOOD RESOLUTION LOOKS LIKE:
{{RESOLVED}}

CONTEXT:
{{CONTEXT}}

Think strictly within your framework. Do not hedge into other lenses, do not try to
be balanced, and do not soften your analysis to be agreeable — other seats cover the
other angles. Perform your framework's mandated move. Be concrete and specific to THIS
problem; generic advice is failure.

Return ONLY a JSON object matching this schema (this JSON is authoritative; a short
human-readable summary MAY follow it but the JSON is what gets parsed):

{
  "seat": "{{SEAT_NAME}}",
  "position": "<your recommendation/answer on the problem, in 1-3 sentences>",
  "key_reasoning": ["<bullet>", "<bullet>", "..."],
  "mandated_finding": "<the specific move your framework REQUIRES — e.g. the fatal flaw, the wrong-problem call, the biggest upside, the breaking constraint>",
  "assumptions": ["<assumption you are making>", "..."],
  "open_questions": ["<what you'd need to know to be more sure>", "..."],
  "confidence": <integer 0-10>
}
```

## Notes
- `confidence` is the advisor's confidence in its own position, not a vote.
- `mandated_finding` must be non-empty and substantive; an advisor that leaves it vague has not done its job.
- Keep `key_reasoning` to the points that actually follow from the framework — 3 to 6 bullets is typical.
