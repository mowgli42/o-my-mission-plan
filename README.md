# o-my Mission Plan

**Mission planning capability for the Open Arsenal / o-my OMS ecosystem.**

Prototype for iterative “guess-and-see” mission planning cycles:

- Simulate ATO ingestion → pool of unassigned collection (ISR) and strike tasks
- Simple task allocation: group tasks by region and assign to suitable aircraft (ISR / fighter / bomber) that have a home airbase
- Initial route generator that builds legs using **commercial navaid points**
  - ~80 nmi legs for ISR / collection tasks
  - ~20 nmi legs for strike tasks
- FastAPI **Route Propagation Service** that tracks fuel remaining and burn rate per leg so the platform can safely complete the route
- Designed so external suppliers can later implement richer services (full ATO parse, advanced allocation, loadout determination, optimization) and talk to this core via **UCI messages**

---

## Status

**Scaffold + design in progress.**  
Living OpenSpec + Gherkin + Beads coming in the first commits.

| Capability | Status |
|------------|--------|
| OpenSpec + Gherkin acceptance scenarios | Planned |
| Beads epic + phased issues | Planned |
| Mock ATO → unassigned task pool | Planned |
| Simple regional task allocator | Planned |
| Initial route generator (navaids + fixed leg distances) | Planned |
| Route Propagation Service (FastAPI + fuel/burn) | Planned |
| Dynamic task insertion + re-propagation | Planned |
| Demo world (Central/East Florida navaids + airbases) | Planned |

---

## Design Principles

1. **Keep the core small.** The Route Propagation Service is the single source of truth for live routes + fuel state.
2. **Iterative by nature.** Mission planning is a series of “guess what is possible” cycles. The prototype must make those cycles fast and visible.
3. **UCI-first contracts.** Everything that will eventually be an external supplier service publishes/consumes UCI-aligned messages.
4. **Demo realism without complexity.** Use real commercial navaids and realistic airbase locations in Florida; keep distances and burn models deliberately simple.

---

## Related repos

- [`o-my`](https://github.com/mowgli42/o-my) — C2 / UCI bus processors
- [`o-my-debrief`](https://github.com/mowgli42/o-my-debrief) — Platform debrief (same OpenSpec + Beads + FastAPI/Svelte pattern)
- [`o-my-sim`](https://github.com/mowgli42/o-my-sim) — publishers / scenario clock (when available)
- [`fuzzy-reconciler`](https://github.com/mowgli42/fuzzy-reconciler) — reference OpenSpec + Svelte/FastAPI layout

---

*Open Arsenal — Open by Design • Agile by Default*
