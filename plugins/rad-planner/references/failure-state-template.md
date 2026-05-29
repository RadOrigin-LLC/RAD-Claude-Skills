# Failure State Mapping: Triple-Component Instructions

AI models suffer from "happy path" bias -- they assume every tool call, API response, and environment configuration will succeed perfectly. The planner must counter this by defining explicit failure states for every milestone or risky change. In a v4.x plan these map onto `docs/planning/current.md`'s **Validation commands** (the check), **Stop conditions** (when to escalate rather than push on), and **Guardrails** (what must not change).

## The Triple-Component Model

Every milestone or risky change requires three components:

### 1. Execution Action
The precise technical operation to be performed.
- Must be specific enough that an agent can execute it without interpretation
- Include the exact command, file path, or API call
- Specify expected inputs and outputs

### 2. Validation Check
A deterministic test or status probe confirming success.
- Must be automatable (runnable command, not "looks right")
- Must produce a clear pass/fail signal
- Should check both the positive case AND key negative cases
- Include expected output or exit code

### 3. Rollback Procedure
Pre-determined reversal steps to revert to the last stable state.
- Must be tested before the execution action runs
- Should restore the system to the exact pre-execution state
- Include data recovery steps if destructive operations are involved
- Specify what constitutes a "clean rollback" vs. "partial recovery"

## Template (per milestone or risky change)

```markdown
#### Example: user authentication middleware

**Execution Action:**
Create JWT validation middleware in `src/middleware/auth.ts` that:
- Extracts Bearer token from Authorization header
- Validates token signature against `JWT_SECRET`
- Attaches decoded user payload to request context
- Returns 401 for missing/invalid tokens

**Validation Check:**
```bash
# Run auth middleware tests
npm test -- --grep "auth middleware"

# Expected: All tests pass
# - Valid token: request proceeds, user attached to context
# - Missing token: returns 401 with error message
# - Expired token: returns 401 with "token expired" message
# - Malformed token: returns 401, does not crash server
```

**Rollback Procedure:**
```bash
# Remove the middleware file
git checkout -- src/middleware/auth.ts

# Revert route registrations that depend on it
git checkout -- src/routes/index.ts

# Verify server starts without auth middleware
npm run dev
```

**User Checkpoint:** Review middleware logic before integrating into routes. Verify token validation matches your auth provider's signing algorithm.
```

## Failure State Categories

### Environment Failures
- Missing environment variables
- Incorrect database connection strings
- Port conflicts
- Missing system dependencies

### Data Failures
- Schema migration failures (column conflicts, data loss)
- Seed data incompatible with schema changes
- Foreign key constraint violations
- Data type mismatches

### Integration Failures
- API endpoint not responding
- Authentication token expired or invalid
- Rate limiting triggered
- Network timeout

### Logic Failures
- Test assertions failing (implementation doesn't match spec)
- Edge cases not handled (null inputs, empty arrays, boundary values)
- Race conditions in async operations
- State management inconsistencies

## Checkpoint Frequency

Insert validation checkpoints:
- After every milestone completion
- After any change that modifies database schema
- After any change to authentication / authorization
- After any change that integrates with external services
- Before any destructive or irreversible operation

## Escalation Protocol

If a validation check fails:
1. **First attempt:** Review error output, identify root cause, fix and re-validate
2. **Second attempt:** If same failure, check anti-patterns list -- the approach may be fundamentally wrong
3. **Third attempt:** STOP. Do not retry. Execute rollback procedure. Surface the failure to the user via the milestone's stop conditions, with a clear description of what failed and why. Escalate to human review.

Never enter an endless correction loop. After 2 failures on the same task, the context is likely polluted. Clear and restart with a fresh approach.
