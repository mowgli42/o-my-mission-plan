# o-my Mission Plan

**Mission planning capability for the Open Arsenal / o-my OMS ecosystem.**

Functional prototype for iterative “guess-and-see” mission planning cycles in a
**Gulf War / PSAB launch** scenario:

- Simulate ATO ingestion → pool of unassigned collection (ISR) and strike tasks across **Kuwait and Iraq**
- Aircraft all launch from **Prince Sultan AB (PSAB / OEPS)**
- Simple task allocation: group tasks by region and assign to suitable aircraft (ISR / fighter / bomber)
- Initial route generator that sequences **published waypoints** (airbases + commercial navaids + fixed mission fixes)
  - proximity success criteria: within **80 nmi** of ISR / collection tasks
  - within **20 nmi** of strike tasks
  - never invents runtime `PROX-*` lat/lon points (see [`docs/ROUTE-GENERATION.md`](docs/ROUTE-GENERATION.md))
- FastAPI **Route Propagation Service** that tracks fuel remaining and burn rate per leg
- **Export final GO routes** as JSON for **o-my-sim** to import and publish on `uci.route` when aircraft launch (see [`docs/OMY-SIM-ROUTES.md`](docs/OMY-SIM-ROUTES.md))
- Dark-theme planning console guided by **IxDF / Nielsen usability heuristics**

---

## Status

**Functional prototype implemented** (scenario: `gulf-war-psab-001`).

| Capability | Status |
|------------|--------|
| OpenSpec + Gherkin acceptance scenarios | Done |
| Beads epic + phased issues | Done |
| Gulf War / PSAB demo world (Kuwait & Iraq tasks) | Done |
| Mock ATO → unassigned task pool | Done |
| Simple regional task allocator | Done |
| Initial route generator (published waypoints + proximity check) | Done |
| Route Propagation Service (FastAPI + fuel/burn) | Done |
| Dynamic task insertion + re-propagation | Done |
| Final route export for o-my-sim (`uci.route` on launch) | Done |
| Dark-theme IxDF planning UI | Done |
| Unit / API tests | Done (`make test`) |

---

## Quick start

```bash
python3 -m pip install -e ".[test]"
make demo
# open http://localhost:8000
# API docs: http://localhost:8000/docs
```

1. **Run plan cycle** (or press `P`)
2. **Export for o-my-sim** (or press `E`) → writes `data/routes/gulf-war-psab-001-routes-latest.json`
3. Point o-my-sim at that file; it publishes each GO route on launch

Keyboard shortcuts: **P** plan · **E** export · **I** insert strike · **R** reset · **?** help.

---

## What's implemented

### Backend (`src/omy_mission_plan/`)

| Module | Role |
|--------|------|
| `models.py` | Aircraft, Task, Route, FuelState, AllocationResult, … |
| `demo_world.py` | PSAB launch, Kuwait/Iraq tasks, navaids + mission waypoints |
| `allocator.py` | Regional grouping + type-capable assignment; always returns unallocated ids |
| `route_generator.py` | Home → published fixes → home (proximity validated; no PROX-*) |
| `propagator.py` | Constant burn + fixed reserve → GO / NO-GO |
| `planning.py` | Full plan cycle + dynamic insert |
| `export_routes.py` | o-my-sim import bundle (`o-my.mission-plan.routes/v1`) |
| `app.py` | FastAPI service + static UI |

### API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness |
| GET | `/api/world` | Demo fixtures snapshot (scenario + mission waypoints) |
| POST | `/api/reset` | Reset in-memory world |
| POST | `/api/plan` | Allocate → route → fuel propagate |
| GET | `/api/plan` | Latest plan result |
| POST | `/api/tasks/insert` | Inject task; full re-assess for one aircraft |
| POST | `/api/propagate` | Fuel-propagate an arbitrary route |
| POST | `/api/routes/export` | Write final GO routes for o-my-sim |
| GET | `/api/routes/export` | Build export bundle without writing |
| GET | `/` | Dark planning UI |
| GET | `/docs` | Swagger |

### Docs

- [`docs/DEMO-WORLD.md`](docs/DEMO-WORLD.md) — PSAB / Kuwait / Iraq scenario
- [`docs/ROUTE-GENERATION.md`](docs/ROUTE-GENERATION.md) — published-waypoint-only design
- [`docs/OMY-SIM-ROUTES.md`](docs/OMY-SIM-ROUTES.md) — export contract for o-my-sim
- [`docs/examples/gulf-war-psab-001-routes-example.json`](docs/examples/gulf-war-psab-001-routes-example.json) — sample bundle

### UI (IxDF principles)

Dark ops console emphasizing status visibility (GO / NO-GO, fuel bars), real-world
theater language (PSAB, Kuwait, Iraq), export for sim handoff, and recoverable
NO-GO / unallocated feedback.

---

## Screenshots

Screenshots under `docs/screenshots/` were captured from an earlier Florida demo UI;
re-run `make screenshots` after `make demo` to refresh for the PSAB theater map.

---

## Design Principles

1. **Keep the core small.** The Route Propagation Service is the single source of truth for live routes + fuel state.
2. **Iterative by nature.** Mission planning is a series of “guess what is possible” cycles.
3. **UCI-first contracts.** Final routes are exported so o-my-sim can publish `uci.route` on launch.
4. **Demo realism without complexity.** PSAB launch + published Gulf theater fixes; burn models stay deliberately simple.

---

## Tests

```bash
make test
```

---

## Related repos

- [`o-my`](https://github.com/mowgli42/o-my) — C2 / UCI bus processors
- [`o-my-debrief`](https://github.com/mowgli42/o-my-debrief) — Platform debrief
- [`o-my-sim`](https://github.com/mowgli42/o-my-sim) — publishers / scenario clock (imports routes from this service)
- [`fuzzy-reconciler`](https://github.com/mowgli42/fuzzy-reconciler) — reference OpenSpec + FastAPI layout

## License

See [LICENSE](LICENSE).
