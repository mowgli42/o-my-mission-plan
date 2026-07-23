# o-my-mission-plan — project context

## Mission

Provide a lightweight, iterative mission-planning capability for the o-my / Open Arsenal OMS ecosystem.

The system supports “guess-and-see” planning cycles:
1. Simulate ATO ingestion into a pool of unassigned ISR (collection) and strike tasks.
2. Allocate groups of tasks in a region to suitable aircraft (ISR / fighter / bomber) that have an assigned home airbase.
3. Generate an initial route that visits the tasks using commercial navaid points, with characteristic leg lengths (~80 nmi for ISR, ~20 nmi for strike).
4. Hand the route to a FastAPI **Route Propagation Service** that tracks fuel remaining and burn rate per leg and answers “can this platform safely complete the remaining route?”
5. During execution, accept a newly identified task, re-insert it, and re-propagate fuel/legs.

Richer capabilities (full ATO parsing, advanced allocation algorithms, loadout determination, multi-ship deconfliction, threat avoidance, optimization) are intentionally left for external supplier services that will interface via UCI messages.

## Stack (planned)

| Layer | Choice |
|-------|--------|
| Core service | FastAPI + Pydantic |
| Task allocation & route generation | Pure Python (simple rules) |
| Persistence (prototype) | In-memory + optional JSON fixtures |
| Tracking | Beads (`bd`) + OpenSpec + Gherkin |
| Future UI | Svelte 5 (map + fuel state) — not required for first prototype |

## Related repos

- `o-my` — C2 / UCI bus processors
- `o-my-debrief` — Platform debrief (same OpenSpec + Beads pattern)
- `o-my-sim` — publishers / scenario clock
- `fuzzy-reconciler` — reference OpenSpec + FastAPI layout

## Conventions

- Topics / messages align with UCI style used in `o-my` (`uci.platform.status`, `uci.task`, `uci.route`, …).
- Demo world: Central / East Florida (real commercial navaids + realistic airbases).
- API base path: `/api/*`, Swagger at `/docs`.
