# Task Beads — o-my Mission Plan

Issue DB: `.beads/` · prefix `omp` · run `bd ready` / `bd list`.

## Epic (to be created)

**`omp-…`** — MVP: Mission planning prototype (allocator + route generator + fuel propagator)

### Planned phases

| Phase | Focus |
|-------|-------|
| 1 | Demo world (Florida navaids + airbases + sample tasks/aircraft) |
| 2 | Mock ATO → unassigned task pool |
| 3 | Simple regional task allocator |
| 4 | Initial route generator (navaid legs, 80 nmi ISR / 20 nmi strike) |
| 5 | FastAPI Route Propagation Service (fuel + burn rate per leg) |
| 6 | Dynamic task insertion + re-propagation |
| 7 | Docs, tests, Swagger examples |

## Workflow

```bash
bd ready
bd update <id> --claim
bd close <id>
```
