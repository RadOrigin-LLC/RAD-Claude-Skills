---
name: add-resource
description: >
  Register a project resource (MCP server, CLI tool, script, or note) into
  CLAUDE.md's Resources section so `/startup` surfaces it every session. Creates
  the Resources section if missing. Trigger when the user says "/add-resource",
  "add to project resources", "remember this MCP for the project", "save this
  tool to CLAUDE.md", "register this resource", "remember we have X available
  here", "add X to the resources section".
allowed-tools:
  - Read
  - Edit
  - Write
  - Glob
---

# Add Resource

Append a user-supplied resource to `CLAUDE.md`'s canonical `## Resources` section so it becomes part of the project's permanent state and is surfaced by `/startup` on every new session.

**This skill only writes to CLAUDE.md at the project root. It never touches other files.**

**Cross-model note.** Model-agnostic. Always use targeted `Edit` operations to insert single lines rather than `Write` to rewrite the whole file — whole-file rewrites churn trailing whitespace and line endings on Windows, inflate diffs, and risk clobbering manual edits the user made between sessions.

---

## Phase 1: Parse the Request

Extract from the user's message:

1. **Category** — which sub-bucket the resource belongs to:
   - `MCPs` — MCP servers (e.g., "supabase", "coolify", "stripe")
   - `Stack CLIs` — command-line tools available for this project (e.g., "supabase CLI", "gh", "wrangler")
   - `Scripts` — npm/pnpm/make targets worth remembering
   - `Notes` — freeform resource notes that don't fit above (e.g., "API docs at https://...", "staging DB creds in 1Password item 'X'")

2. **Name/value** — the specific thing to register. Accept a short label plus an optional description.

3. **Optional context** — version, URL, or a one-line "when to use" hint.

If the user's message is ambiguous (e.g., just "remember this"), ask one clarifying question:

> Which category? MCP server, CLI tool, script, or a freeform note?

Do not proceed until the category is clear.

---

## Phase 2: Locate or Create the Resources Section

### 2.1 Read CLAUDE.md

Read `CLAUDE.md` at the project root.

- **If CLAUDE.md does not exist:** create a minimal scaffold first:
  ```markdown
  # [Project Name — from directory name]

  ## Tech Stack
  [TBD]

  ## Conventions
  [To be established]

  ## Resources
  ```
  Then proceed to Phase 3.

- **If CLAUDE.md exists but has no Resources section:** append a new `## Resources` section at the end of the file (after the last existing section). Use this structure:

  ```markdown
  ## Resources

  **MCPs:**

  **Stack CLIs:**

  **Scripts:**

  **Notes:**
  ```

  Only include the sub-buckets that will have content. Empty sub-buckets can be omitted — re-add them when needed.

- **If CLAUDE.md has a Resources section under a different alias** (`## MCP`, `## Tools`, `## CLI Tools`): **use the existing section as-is** — do not rename it. Respect the user's chosen heading. Add the new entry under the most appropriate sub-bullet or create one.

### 2.2 Canonical Structure

Within the Resources section, organize entries using bold sub-labels, not sub-headings, so the section stays scannable:

```markdown
## Resources

**MCPs:**
- `supabase` — Supabase MCP server; use for DB queries, migrations, edge function deploys
- `coolify` — Coolify MCP; deploy, logs, env vars for this project's staging/prod

**Stack CLIs:**
- `supabase` — local DB, migrations, types generation
- `gh` — PR management, issue triage
- `docker` — local compose stack

**Scripts (pnpm):**
- `dev` — start local dev server
- `test` — run vitest
- `typecheck` — tsc --noEmit

**Notes:**
- Staging DB credentials: 1Password vault "Project X" → item "Staging DB"
- API docs: https://docs.example.com/api/v2
```

**Format rules:**
- One entry per line, bullet form
- Name in backticks, em-dash, short description
- Keep descriptions under ~80 chars
- Order within a sub-bucket is insertion order (newest at bottom)

---

## Phase 3: Append the Entry

### 3.1 De-duplication

Before writing, scan the target sub-bucket for an existing entry with the same name:

- **Exact match** — do nothing, tell the user: `"<name>" is already registered under <category>.`
- **Name match with different description** — ask: `"<name>" already exists with description "<old>". Replace with "<new>"? (yes/no)`
- **No match** — proceed to append.

### 3.2 Write

Use `Edit` to insert the new line at the bottom of the correct sub-bucket. **Do not use `Write` to rewrite the entire CLAUDE.md** — targeted `Edit` preserves everything else byte-for-byte. If the sub-bucket does not yet exist within the Resources section, add it (still via `Edit`, anchored on the section heading) in the order: MCPs → Stack CLIs → Scripts → Notes.

### 3.3 Show the Change

After writing, present the diff compactly:

```
Added to CLAUDE.md Resources:

**MCPs:**
+ `stripe` — Stripe MCP; billing, subscriptions, webhook inspection

Saved. /startup will include this in future session briefings.
```

---

## Phase 4: Multi-Entry Batching

If the user asks to add several resources in one request (e.g., "remember we have supabase MCP, stripe MCP, and the gh CLI"), process them as a batch:

1. Parse each entry and classify its category
2. De-duplicate each against existing entries
3. Write all new entries in a single `Edit` if possible
4. Show a consolidated diff:

   ```
   Added to CLAUDE.md Resources:

   **MCPs:**
   + `supabase` — ...
   + `stripe` — ...

   **Stack CLIs:**
   + `gh` — ...

   Saved 3 resources. /startup will include these in future session briefings.
   ```

---

## Rules

- **Never modify sections outside of `## Resources`** (or its aliases). This skill has one job.
- **Never remove or rename existing entries** unless the user explicitly says "remove" or "replace".
- **Never prune or reformat** the Resources section — only append or replace targeted entries.
- **Never read `.env` or any file with real secret values** — if the user asks to save a secret, refuse and suggest they note the **location** of the secret instead (e.g., "1Password item X").
- **Confirm before overwriting** an existing entry with the same name.
- **Work at project root only** — do not walk into subdirectories looking for CLAUDE.md files.

## Completion

End with one line:

```
Saved. Run /startup next session to see it in the briefing.
```
