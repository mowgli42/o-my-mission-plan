# Concept of Operations — o-my Mission Plan

## Purpose

Mission planning is an **iterative “guess-and-see” cycle**. The planner does not produce a single definitive route on the first pass. Instead the system supports generating, saving, comparing, and refining multiple planning options until the commander accepts a set that balances efficiency, synchronized effects, and operational surprise.

This CONOPS defines:

1. The planning cycle and how progress is tracked
2. The **top-three mission option set** the planner keeps visible
3. How router inputs are persisted so options can be re-run and compared
4. How comparison drives the next iteration

Demo theater for the prototype: launch from **OEPS (Prince Sultan AB / PSAB)** into Kuwait / Iraq task areas (see current Gherkin). The same cycle applies to any theater once the navigation database and task pool are swapped.

---

## 1. Planning cycle (progress trackable)

```text
┌──────────────┐
│ 0. Ingest    │  Simulate ATO → unassigned ISR + strike task pool
└──────┬───────┘
       ▼
┌──────────────┐
│ 1. Frame     │  Select objective emphasis for this pass
│              │  (efficient | synchronized | unexpected-axis)
└──────┬───────┘
       ▼
┌──────────────┐
│ 2. Allocate  │  Regional grouping → aircraft; report unallocated
└──────┬───────┘
       ▼
┌──────────────┐
│ 3. Route     │  Supplier or fallback builds published-waypoint routes
│              │  (router inputs saved with the option)
└──────┬───────┘
       ▼
┌──────────────┐
│ 4. Propagate │  Fuel + reserve → GO / NO-GO per aircraft
└──────┬───────┘
       ▼
┌──────────────┐
│ 5. Compare   │  Score / side-by-side vs other saved options
└──────┬───────┘
       ▼
┌──────────────┐
│ 6. Decide    │  Keep / refine / discard; optionally inject new task
│              │  and re-enter at step 2 or 3
└──────────────┘
```

Each completed pass produces a **Mission Option** that is stored and remains available for comparison. Progress is the set of options under consideration plus their GO/NO-GO and comparison scores—not a single boolean “plan complete.”

---

## 2. Top-three mission options (always retained)

The planner maintains up to **three named options** as the working set. They are not mutually exclusive aircraft assignments; they are alternative holistic plans for the same (or largely overlapping) task pool so the planner can trade off different operational intents.

| Slot | Name | Intent | Typical router bias |
|------|------|--------|---------------------|
| **A** | Efficient | Minimize total distance / fuel / time while still covering assigned tasks | Direct-ish published-waypoint sequences; shortest feasible paths; few extra vias |
| **B** | Synchronized effects | Time-align strikes, sequence BDA/collection after strike, support simultaneous or staggered effects | Shared timing windows, common IP/hold points, ISR routed to observe post-strike; may accept longer legs |
| **C** | Unexpected axis | Approach from a non-obvious direction (e.g. not straight from PSAB to target, but north via Jordan then east/west into the target area) | Forced vias / corridor constraints that encode the desired axis; cost or hard constraints on the “obvious” corridor |

Example of C (narrative): instead of a direct PSAB → target radial, the route climbs north toward a Jordan corridor and enters the target area from the west so the approach axis is not the one the adversary expects from the main operating base.

The UI and API should always expose these three slots (populated or empty) so the planner can see “what we have so far” for each intent.

---

## 3. Saved router inputs (iterative planning)

Every Mission Option stores the **inputs that produced it**, not only the resulting routes:

- Task set (ids) considered for this option
- Aircraft set and home bases
- Objective emphasis (efficient | synchronized | unexpected-axis)
- Supplier id / mode (`fallback` | `openroutefinder` | `costgrid` | …)
- Router parameters: optional vias, corridor / avoid polygons, timing windows (for synchronized), approach-axis constraints (for unexpected)
- Timestamp and human label

Re-running an option with a small parameter change (new via, tighter timing, extra avoid zone) must be possible without rebuilding the entire world state from scratch. Dynamic task insertion still forces full re-generation for the affected aircraft inside the option being edited.

---

## 4. Comparison method

Comparison is deliberately lightweight in the prototype and can grow:

| Dimension | Efficient (A) | Synchronized (B) | Unexpected (C) |
|-----------|---------------|------------------|----------------|
| Total distance / fuel | Primary | Secondary | Secondary |
| End-fuel margin (vs reserve) | Required GO | Required GO | Required GO |
| Unallocated / unsatisfied tasks | Count + list | Count + list | Count + list |
| Timing alignment (strike TOTs, BDA lag) | N/A or weak | Primary | N/A or weak |
| Approach-axis / corridor match | N/A | N/A | Primary |
| Qualitative notes | Free text | Free text | Free text |

Minimum viable comparison for the prototype:

- Side-by-side table: per-option GO/NO-GO counts, total distance, unallocated count, one-line intent label
- Ability to pin/unpin an option into a slot (A/B/C)
- Ability to duplicate an option, change one router input, and re-propagate for a new candidate

No multi-objective solver is required in v1; the human planner remains in the loop.

---

## 5. Relationship to civil vs mission route generation

- **Civil-style generation** (published airways/waypoints, Dijkstra over nav graph — e.g. openRouteFinder) is the default engine behind **Efficient (A)** and a building block for the others.
- **Mission route generation** adds constraints the civil graph does not know: task proximity, synchronized timing, forced approach axes, threat/avoid regions. Those constraints are expressed as router inputs (vias, corridors, windows) and may be satisfied by a cost-grid supplier or by constrained use of the civil supplier.
- Fuel feasibility always stays in the **Route Propagation Service** after the lateral path is chosen.

See `docs/CIVIL-ROUTE-DEV-GUIDE.md`, `docs/MISSION-ROUTE-DEV-GUIDE.md`, and `docs/SUPPLIER-ROUTE-TOOLS.md`.

---

## 6. Progress tracking

A planning session is “progressing” when:

1. At least one option exists in a top-three slot with GO routes for the critical tasks, or
2. The planner has explicitly compared ≥2 options and recorded a preference / next experiment, or
3. Unallocated / unsatisfied tasks are shrinking across successive iterations, or
4. A dynamic insert has been absorbed into an option and re-validated.

Export to o-my-sim / UCI only occurs for routes the planner has marked accepted from a chosen option (typically after comparison).

---

## 7. Non-goals for the CONOPS prototype

- Fully automated selection of the “best” of the three options
- Perfect multi-ship deconfliction or tanker planning
- Real-time re-planning under live threat tracks (future supplier)
- Replacing human judgment on synchronized effects or deception axes
