# Agentic UX Patterns — 2026 Reference

In 2026, AI is invisible infrastructure that takes multi-step autonomous actions. This requires a new UX vocabulary. The three core patterns below — Intent Preview, Autonomy Dial, Action Audit & Undo — are the trust floor for any agentic interface.

## Pattern 1: Intent Preview

### What it is
Before the agent acts, show the user a summary of the action — the verb, the objects, the parameters — in plain language.

### Why
Closes the gap between user intent and AI interpretation. Catches misunderstandings cheaply.

### Implementation

```jsx
function IntentPreview({ action }) {
  return (
    <div role="dialog" aria-labelledby="preview-title">
      <h2 id="preview-title">Confirm action</h2>
      <p>I'll <strong>{action.verb}</strong> the following:</p>
      <ul>
        {action.objects.map(o => <li key={o.id}>{o.label}</li>)}
      </ul>
      {action.params && (
        <dl>
          {Object.entries(action.params).map(([k, v]) => (
            <Fragment key={k}>
              <dt>{k}</dt><dd>{v}</dd>
            </Fragment>
          ))}
        </dl>
      )}
      {action.assumptions && (
        <details>
          <summary>What I inferred</summary>
          <ul>{action.assumptions.map(a => <li key={a}>{a}</li>)}</ul>
        </details>
      )}
      <button onClick={action.confirm}>Confirm</button>
      <button onClick={action.cancel}>Cancel</button>
    </div>
  );
}
```

Key UX rules:
- Echo the user's words where possible
- Surface inferred defaults (so the user can correct them)
- Confirmation must be a deliberate click — never Enter-key autofire
- Support keyboard cancel (Escape)

## Pattern 2: Autonomy Dial

### What it is
User-controlled setting for how independently the agent operates. Per-task or per-task-class.

### Levels (typical 4-level)

| Level | Behavior | Use case |
|---|---|---|
| **Suggest** | Agent proposes; user clicks to act | Risk-averse, learning new agent |
| **Confirm** | Agent prepares; user confirms each | Default for trust-building |
| **Notify** | Agent acts; user gets notified after | Routine, low-stakes |
| **Auto** | Agent acts silently within boundaries | High trust, repetitive tasks |

### Implementation

```jsx
function AutonomyDial({ value, onChange, taskClass }) {
  return (
    <fieldset>
      <legend>Agent autonomy for {taskClass}</legend>
      {['suggest', 'confirm', 'notify', 'auto'].map(level => (
        <label key={level}>
          <input
            type="radio"
            name={`autonomy-${taskClass}`}
            value={level}
            checked={value === level}
            onChange={() => onChange(level)}
          />
          {LEVEL_LABELS[level]}
          <span className="hint">{LEVEL_HINTS[level]}</span>
        </label>
      ))}
    </fieldset>
  );
}
```

### Rules

- **Default to Confirm** for new users — never default to Auto
- Per-task-class granularity: a user might want Auto for "categorize email" but Confirm for "respond to email"
- Show the **current dial position** in the surface where the agent acts (not just settings)
- Allow per-action override ("Just for this one — auto") that doesn't change the persistent setting

## Pattern 3: Action Audit & Undo

### What it is
Persistent, scrollable log of agent actions, with reversal where possible.

### Why
Every autonomous action must be reviewable and (where feasible) reversible. This is the safety net that lets users grant higher autonomy.

### Implementation

```jsx
function ActionAudit({ entries }) {
  return (
    <ol className="audit-log" aria-label="Recent agent actions">
      {entries.map(entry => (
        <li key={entry.id}>
          <time dateTime={entry.timestamp}>{formatTime(entry.timestamp)}</time>
          <span className="actor">{entry.actor === 'agent' ? 'Agent' : 'You'}</span>
          <span className="verb">{entry.verb}</span>
          <span className="object">{entry.object}</span>
          {entry.reversible && (
            <button onClick={() => reverse(entry.id)}>Undo</button>
          )}
        </li>
      ))}
    </ol>
  );
}
```

### Rules

- Persist beyond session (use IndexedDB / server) — not just in-memory
- Filter by actor (agent vs user), date, action type
- Export for compliance contexts (regulated industries)
- For irreversible actions: do NOT rely on audit-log-only — require explicit confirmation BEFORE the action

## When to require human confirmation regardless of dial

Even at Auto, these MUST require explicit human confirmation:

- Irreversible financial transactions (purchases, transfers, refunds)
- Data deletion (accounts, files, messages, history)
- High-stakes domains (medical advice, legal advice, contractual signing)
- Identity actions (password resets, role changes)
- Cross-account actions (sharing, posting on behalf, granting access)

## Cmd+K command palette

For any web app with >10 features:

```jsx
function CommandPalette({ open, onClose }) {
  return (
    <Dialog open={open} onClose={onClose}>
      <input
        autoFocus
        placeholder="Type a command, search, or ask..."
        aria-label="Command palette"
      />
      <ul role="listbox">
        {/* Recent + suggested + AI */}
      </ul>
    </Dialog>
  );
}
```

Hotkeys: Cmd+K (Mac) / Ctrl+K (Win/Linux). Show the hotkey in the trigger UI.

Surface AI suggestions inline: "Generate report from last week's data" alongside indexed commands.

## Multimodal handoff

Voice-only is largely obsolete in 2026. The 2026 standard is **multimodal** with explicit handoffs:

- Default to visual interaction
- Promote to voice when: hands-busy, accessibility better served, public-space privacy not a constraint
- Show a state indicator: "Listening..." vs "Showing results" — never ambiguous

## Sycophancy avoidance

- Train the agent to surface uncertainty: "I'm not sure — here's what I found, you decide."
- Allow disagreement: "I think this won't work because X. Want me to try anyway?"
- Optimize for accuracy over satisfaction in eval criteria

A sycophantic agent that flatters and agrees inflates short-term satisfaction scores but destroys trust permanently when users detect the manipulation. See `web-design-anti-patterns` Tier 1 #2.

## Anti-patterns (cross-ref)

- Sycophantic AI assistants → AVOID-AT-ALL-COSTS #2
- Auto-fired actions without preview → forces users to undo rather than approve
- Hidden audit trails → undermines the entire autonomy model
- Irreversible defaults → high-cost mistakes for nothing gained

## Sources

NotebookLM "Web Design" (2026) + Anthropic Claude documentation on agentic patterns + 2026 web research on AI-native UX.
