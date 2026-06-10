# docs/reference/ — the closed reference catalog

On-demand authority. These docs are **not** read every session — only when a task
touches the area. The catalog is a fixed menu of slots, not a free-for-all folder: a
doc that matches a slot is filed here; anything off-catalog is itself a loose end.

| Slot | What goes in it |
|---|---|
| `decision-log.md` | active decisions, compact (the quick "what did we decide about X?") |
| `architecture.md` | system shape, data model, stack rationale |
| `api-contracts.md` | API routes, provider / AI integration contracts |
| `commands.md` | build / release / deployment commands |
| `lessons-learned.md` | known traps and their fixes |
| `testing.md` | test strategy / coverage |

Brand / UI/UX / visual design direction lives at top-level `docs/design.md`, not here
— and technical/system design lives in `architecture.md`, never in `design.md`.

Each reference doc appears only when the project needs it — this catalog is the menu,
not the starter set. Create a slot's file when you first have real content for it;
leave the rest absent.
