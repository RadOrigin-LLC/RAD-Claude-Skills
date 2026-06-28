# Security-Deep Review Mode (Launch-Readiness)

> Drop-in mode reference for RADCR. Loaded by the orchestrator when invoked with
> `--security-deep`, or when strictness is set to `launch`. This document is the
> complete operating spec for the mode: purpose, procedure, the threat-model-lite
> report section, the no-false-assurance contract, and invocation wiring.
>
> This mode does NOT replace the standard security checklist
> (`references/security-checklist.md`) — it runs *on top of it* with a narrowed
> lens and a stricter output contract. Load both, and lean on
> **security-checklist §2.5** for the BaaS data-exposure detail.

---

## 1. Purpose & Scope

Security-deep is a focused launch-readiness mode for a developer about to put real
customer data behind a stack — most acutely a Backend-as-a-Service (BaaS) stack
(Supabase, Firebase, Appwrite, PocketBase, AWS Amplify, Nhost) where the database
client often runs *in the browser* and the only thing standing between a stranger
and every customer row is a row-level-security policy the developer may have
forgotten to turn on. This mode **de-prioritizes style, performance, nits, and most
code-quality findings** (report them only if they directly create exposure) and
concentrates the entire review budget on three surfaces: (a) the **data-exposure
surface** — every path by which a row of customer data can leave the system; (b) the
**authorization model** — where enforcement actually lives (server middleware?
database RLS/rules? both? neither?) and whether it holds at every trust boundary; and
(c) **secrets & privileged credentials** — anything that, if leaked or misused,
collapses the authorization model entirely (e.g. a `service_role`/admin key shipped
to the client). The mode targets expert-level data-exposure and authorization
assurance: "looks fine" is a failing grade.

---

## 2. Procedure

The reviewing subagent runs these four phases **in order**. Do not skip ahead —
phase (a) produces the boundary list that phases (b)–(d) are checked against. Every
finding uses the standard RADCR finding format and the four-level severity model
(critical / major / moderate / minor). Anchor each finding to OWASP API Security
Top 10 (2023) where applicable: **API1 BOLA**, **API3 BOPLA**, **API5 BFLA**,
**API2 Broken Authentication**, **API8 Security Misconfiguration**.

### Phase (a) — Enumerate trust boundaries

Map every place where untrusted input or an untrusted client touches the system.
A trust boundary is any point where data crosses from a less-trusted zone to a
more-trusted one. On a BaaS stack the most dangerous boundary is usually
**browser → database**, because there may be *no server tier in between*.

**Enumerate, with file/line for each:**
- Every HTTP route / API handler / serverless function / edge function entry point.
- Every BaaS client call made **from client-side code** (the browser talks straight
  to the DB/storage — the SDK call site *is* the boundary).
- Every webhook receiver (Stripe, auth providers, queue callbacks).
- Every file/storage upload and download path.
- Every place external/3rd-party data enters (OAuth callbacks, imports, RAG sources).

**Grep starters:**
```
createClient\(|initializeApp\(|new Client\(            # BaaS SDK init — note which key
\.(from|collection|doc|ref|storage|rpc)\(             # supabase/firebase data calls
export (async )?function (GET|POST|PUT|PATCH|DELETE)  # route handlers
app\.(get|post|put|patch|delete)\(                    # express/fastify
NEXT_PUBLIC_|VITE_|EXPO_PUBLIC_|REACT_APP_            # anything bundled to the client
```
For each client-side BaaS call, record **which key initialized the client** (anon/
publishable vs service_role/secret) — phase (d) depends on this.

**Output of this phase:** a numbered boundary list. Every item is the input to (b)–(d).

### Phase (b) — Map the data-exposure surface

For every boundary in (a), trace **every path a row of customer data can leave the
system**. A path is in scope even if you *believe* it is protected — record it and
verify the control in phase (c).

| Exit path | What to trace | Detection |
|---|---|---|
| Direct DB client | Browser-issued query that returns rows | client init key + table; is RLS the *only* control? |
| API / function response | What the handler `return`s / `res.json`s | whole-record serialization vs explicit field allowlist |
| Storage / buckets | Public buckets, signed-URL TTLs, list permissions | `public: true`, `getPublicUrl`, bucket/list policies |
| Logs | Request/response bodies, tokens, PII written to logs | `console.log`, `logger.*` near req/res/user |
| Error messages | Stack traces, DB errors, internal IDs returned to client | `err.message`/`err.stack` in a response; PostgREST `details`/`hint` |
| Client bundle | Secrets, internal endpoints, seed data shipped to browser | `NEXT_PUBLIC_*`, inlined config, source maps |
| Analytics / 3rd party | PII forwarded to Sentry/Segment/etc. | event payloads containing email/id/PII |

**Whole-record exposure (OWASP API3 BOPLA / "Excessive Data Exposure")** is the
single most common BaaS leak after missing RLS. Flag any handler that returns an
entire DB record/model instead of an explicit field allowlist.

```
res\.json\((user|record|data|row|result)\)            # likely whole-record return
select\(\s*['"]\*['"]                                  # select('*') crossing a boundary
return\s+(data|rows|docs)                              # returning raw query result
\.getPublicUrl\(|public:\s*true                        # public storage
err(or)?\.(message|stack)                              # error detail leaving the system
```

| Check | Severity |
|---|---|
| Customer rows reachable by browser with RLS/rules **off** or absent (and grant-reachable) | critical |
| Whole-record/`select('*')` response leaks fields client shouldn't see — **API3 BOPLA** | major |
| Public storage bucket / never-expiring signed URL / open list policy exposing customer files | major (critical if PII/financial/health) |
| Passwords, tokens, or PII written to logs or forwarded to analytics | major |
| Stack trace / PostgREST error `details` returned to client (existence oracle) | moderate |
| Secret or internal endpoint shipped in client bundle | critical |

### Phase (c) — Interrogate the authorization model

First answer one question explicitly and **write the answer into the report**:
**Where is authorization enforced?** — Server middleware only? Database RLS / rules
only? Both (defense in depth)? Or **Neither** (the dangerous answer — and the default
on a fresh BaaS table)?

Then verify enforcement **at every boundary from (a)**. The failure modes map to OWASP:

- **API1 BOLA / IDOR** — a request for a resource by id returns *someone else's* row.
  On BaaS this is "RLS is off, so the anon key reads every row."
- **API5 BFLA** — a privileged *function* (admin action, role change, bulk delete) is
  reachable by a non-privileged user.
- **API3 BOPLA / mass assignment** — client can *write* fields it shouldn't
  (`is_admin`, `role`, `tenant_id`, `balance`) because the insert/update accepts the
  whole object.

**BaaS-specific verification (do this concretely — see security-checklist §2.5):**
- For **every table/collection reachable by a client key**: is RLS / Security Rules
  **enabled**, and is there a policy that actually scopes rows to the caller? Apply
  the §2.5 reachability gate (exposed schema + grant + no restricting policy) before
  rating critical. A `CREATE TABLE` with no matching `ENABLE ROW LEVEL SECURITY` +
  `CREATE POLICY` that is grant-reachable is a finding.
- **Untrusted-claim check (sleeper critical):** does any policy authorize off
  `user_metadata` / `raw_user_meta_data`? That field is end-user-writable — only
  `app_metadata` or a custom-claim hook is trustworthy.
- **Anonymous-auth check:** if anonymous sign-ins are enabled, `authenticated` ≠
  authorized — flag `to authenticated` / `auth.role()='authenticated'` policies with
  no ownership predicate.
- **Join/embed check:** RLS does not traverse JOINs/embeds — every embeddable child
  table needs its own policy.
- Is the identity used in the policy derived server-side (`auth.uid()`, request
  context) and **never** taken from the request body/params?
- For mutations: is there an INSERT/UPDATE policy *and* a column allowlist, so a
  client can't set privileged columns (mass assignment)?
- Is the default **deny**? Routes/tables must opt *in* to being public, not opt out.

```
enable row level security|ENABLE ROW LEVEL SECURITY     # presence per table
create policy|CREATE POLICY                              # is there actually a policy?
create table                                             # cross-ref: every table has RLS?
auth\.uid\(\)|request\.auth                              # identity from trusted context (good)
user_metadata|raw_user_meta_data                         # UNTRUSTED — user-writable claim
\.(insert|update|upsert)\(\s*(req|body|input|data)\b     # whole-object write → mass-assign risk
allow read, write: if true|allow .*: if true             # Firestore: world-open rule
```

| Check | Severity |
|---|---|
| Authorization is "Neither" — client key + grant-reachable table with no RLS/rules — **API1 BOLA** | critical |
| Policy authorizes off `user_metadata` (user-writable) | critical |
| IDOR: resource fetched/mutated by id without owner/tenant scope — **API1** | critical (cross-customer data) |
| `to authenticated` with no ownership predicate while anonymous sign-in is enabled | critical |
| RLS missing on a JOINed/embedded child table | major (critical if PII) |
| Privileged function reachable without role check — **API5 BFLA** | major (critical if it exposes/destroys customer data) |
| Mass assignment: client can write `role`/`is_admin`/`tenant_id`/financial fields — **API3** | major |
| Identity/tenant taken from request instead of trusted context | critical |
| Per-route auth with open default (one missing guard = unauth access) | major |

> **Static-analysis honesty (carry into the report):** RLS/rules verified *from code*
> means "a policy exists and reads correctly." It does **not** prove the policy is
> live in the running project, that it wasn't dropped by a later migration, or that
> it behaves correctly under every role. State this limitation explicitly (§4).

### Phase (d) — Secrets & privileged-credential check

The authorization model is only as strong as the credentials behind it. One leaked
admin key bypasses every policy from phase (c).

- **Privileged BaaS keys must never reach the client.** `service_role` (Supabase),
  Firebase Admin SDK / service-account JSON, Appwrite API keys, AWS secret keys —
  these bypass RLS/rules entirely. A `service_role`/secret key initialized in browser
  code or exposed via a client-bundled env var (`NEXT_PUBLIC_*`, `VITE_*`,
  `EXPO_PUBLIC_*`) is **critical, always**.
- Confirm the client uses only the **anon/publishable** key, and that the anon key's
  safety depends entirely on RLS being correct (ties back to phase (c)). The anon key
  itself in client code is **not** a finding (see §2.5.5).
- Standard secret hygiene: no hardcoded keys, `.env` gitignored, no secrets in git
  history, short-lived where possible.

```
service_role|SERVICE_ROLE|sb_secret_                    # privileged supabase key
serviceAccount|admin\.initializeApp|"private_key"       # firebase admin in wrong tier
NEXT_PUBLIC_.*SERVICE|VITE_.*SECRET|PUBLIC_.*PRIVATE     # secret behind a public-prefixed var
AKIA[0-9A-Z]{16}|sk_live_|-----BEGIN .*PRIVATE KEY      # generic high-value secrets
```

| Check | Severity |
|---|---|
| `service_role` / admin / service-account key in client code or `*_PUBLIC_*`/`VITE_*` env | critical |
| Hardcoded secret / committed `.env` / secret in git history | critical |
| Privileged key used server-side but logged or echoed | major |
| Long-lived key with no rotation path | moderate |

---

## 3. Threat-Model-Lite Output

Security-deep adds a compact threat-model block to the report (decompose → identify →
rank → validate). Keep it tight — this is a map, not an essay.

```markdown
## Threat Model (Lite)

**Stack:** <BaaS + framework, e.g. Supabase + Next.js, browser-direct DB access>
**Authorization enforced at:** <server middleware | RLS/rules | both | NEITHER>

### Trust boundaries
| # | Boundary | Untrusted side | Control that should hold |
|---|---|---|---|
| 1 | Browser → Postgres (anon key) | public internet | RLS policy on table X |
| 2 | POST /api/... | any client | session auth + ownership check |

### Attack surfaces
- <endpoint / table / bucket / function> — <what an attacker would poke>

### Data-flow risks (how a customer row leaves)
- <path> → <control> → <verified? / could-not-verify>

### Single most likely path to a customer-data leak
> One paragraph. Name the one concrete weakness most likely to expose customer data
> on launch day (e.g. "Table `profiles` is reachable by the anon key and migration
> `0007` creates it without ENABLE ROW LEVEL SECURITY — any visitor can `select('*')`
> every user's email"). Tie to the OWASP category (e.g. API1 BOLA) and the finding ID.
```

---

## 4. No-False-Assurance Contract

**This is the most important part of the mode. It is non-negotiable.**

Security-deep is a static, code-only review run by an AI. It can find specific,
demonstrable weaknesses; it **cannot** prove a system is secure.

**The mode MUST:**

1. **Separate verified from could-not-verify.** Every report includes a two-column
   ledger. Be specific about *why* something couldn't be verified.

   | Verified from code | Could NOT verify from static code alone |
   |---|---|
   | Migration `0007` lacks `ENABLE ROW LEVEL SECURITY` for `profiles` | Whether RLS is currently enabled in the *live* project |
   | `service_role` key absent from client bundle | Whether the key leaked previously / is in deploy logs / CI |
   | Ownership filter present on `DELETE /posts/:id` | Whether the policy holds under every role at runtime |
   | Error handler strips stack traces | Behavior of the deployed reverse proxy / WAF |

2. **NEVER emit a "secure" / "safe" / "you're good to launch" / "no issues" verdict.**
   These words are banned from the mode's output. A clean run means "no blocking
   findings were *detected by static review*," not "safe."

3. **State residual risk explicitly**, even when zero blocking findings are found.
   Static code review does not cover live policy state, runtime role behavior,
   deployed infra, prior key leakage, or business-logic auth flaws that require a
   running system to exercise.

4. **Recommend an independent human penetration test** of the authentication,
   authorization, and data-access surface before any launch handling real customer
   data — specifically a test that exercises RLS/rules at runtime with multiple real
   accounts (can user A reach user B's rows?), which static review cannot do.

**Exact honest-verdict wording (use verbatim — pick the line that matches the outcome):**

> **Findings present (blocking):**
> "Security-deep found N blocking data-exposure/authorization issues (listed below).
> This is NOT a clean bill of health — it is a list of what was caught. Even after
> these are fixed, this static review cannot confirm the system is secure: it cannot
> verify live RLS/rules state, runtime authorization behavior across roles, deployed
> infrastructure, or whether any privileged key has already leaked. **Do not launch
> with real customer data until these findings are fixed AND an independent human
> penetration test of the auth and data-access surface has passed.**"

> **No blocking findings detected:**
> "Security-deep detected no blocking data-exposure or authorization issues in the
> reviewed code. **This is not a guarantee that the system is secure, and is not
> permission to launch.** Static code review cannot confirm row-level-security/rules
> are enabled and correct in the live project, cannot exercise authorization across
> real accounts at runtime, and cannot rule out prior credential leakage or
> infrastructure misconfiguration. Residual risk remains. **Before launching with
> real customer data, commission an independent human penetration test of the
> authentication, authorization, and data-access surface — including a live
> cross-account RLS test.**"

Any report that omits the residual-risk statement, omits the pen-test recommendation,
or contains a "secure/safe/good to launch" verdict is itself a **process failure** and
must be regenerated.

---

## 5. Invocation & Report

### Triggering

Two equivalent entry points, both routed to this mode:

- **Flag:** `--security-deep` — runs the mode regardless of project type, layering it
  on the standard security checklist.
- **Strictness level:** `launch` — a new level layered *above* `public`. It inherits
  every `public` blocking rule and adds the security-deep procedure and contract.
  Use `launch` when the project is about to handle real customer data.

```
/rad-code-review --security-deep
/rad-code-review --strictness launch
```

**Release-blocking under `launch`** = everything that blocks at `public`, plus:
- Any critical from phases (b)–(d) (always blocks).
- Any major from the authorization model (phase c) or secrets (phase d).
- A **missing/absent authorization model** ("Neither" in phase c) blocks on its own,
  even with no other findings.
- A report that violates the §4 contract blocks until regenerated.

### New report section

Security-deep inserts one section into the standard report, immediately after the
summary and before the per-finding list:

```markdown
## Launch-Readiness: Data Exposure & Authorization (security-deep)

**Honest verdict:** <verbatim wording from §4 — findings-present OR no-blocking>

[Threat Model (Lite) block from §3]

### Verified vs. Could-Not-Verify
[two-column ledger from §4.1]

### Blocking findings
[standard RADCR findings — security/authorization/secrets only, CR-NNN IDs,
 four-level severity, OWASP API# references]

### Residual risk & required next step
- Residual risk: <explicit statement>
- Required before customer-data launch: independent human penetration test of the
  auth + data-access surface, including a live cross-account RLS/rules test.
```

---

## References

- [OWASP API Security Top 10 (2023) — API1 Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
- [OWASP API Security Top 10 (2023) — API3 Broken Object Property Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)
- [OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
- [Supabase — Understanding API keys (anon/publishable vs service_role/secret)](https://supabase.com/docs/guides/api/api-keys)
- [Supabase — Securing your API (RLS, public schema exposure)](https://supabase.com/docs/guides/api/securing-your-api)
