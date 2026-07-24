# Concept of Operations — o-my Mission Plan

## Purpose

Mission planning is an **iterative “guess-and-see” cycle**. The planner does not produce a single definitive route on the first pass. Instead the system supports generating, saving, comparing, and refining multiple planning options until the commander accepts a set that balances economy of force, synchronized effects, and operational surprise/maneuver.

Options are not only different geometries. They embody different **force engagement approaches** (efficient, synchronized, maneuver/surprise, and optional shock or attrition contingencies). See **`docs/FORCE-APPROACHES.md`** for historical anchors, objectives, and guidelines for each archetype.

This CONOPS defines:

1. The planning cycle and how progress is tracked
2. The **top-three mission option set** (pinned comparison slots) plus a larger contingency pool
3. How router inputs and **approach archetype** are persisted
4. How comparison and (later) gap/risk assessment drive the next iteration

Demo theater for the prototype: launch from **OEPS (Prince Sultan AB / PSAB)** into Kuwait / Iraq task areas (see current Gherkin). The same cycle applies to any theater once the navigation database and task pool are swapped.

---

## 1. Planning cycle (progress trackable)

```text
┌──────────────┐
│ 0. Ingest    │  Simulate ATO → unassigned ISR + strike task pool
└──────┬───────┘
       ▼
┌──────────────┐
│ 1. Frame     │  Select approach archetype + emphasis for this pass
│              │  (efficient | synchronized | unexpected-axis/maneuver |
│              │   shock | attrition | …)
└──────┬───────┘
       ▼
┌──────────────┐
│ 2. Allocate  │  Regional grouping → aircraft; report unallocated
└──────┬───────┘
       ▼
┌──────────────┐
│ 3. Route     │  Supplier or fallback builds published-waypoint routes
│              │  (router inputs + archetype saved with the option)
└──────┬───────┘
       ▼
┌──────────────┐
│ 4. Propagate │  Fuel + reserve → GO / NO-GO per aircraft
└──────┬───────┘
       ▼
┌──────────────┐
│ 5. Compare   │  Side-by-side vs pinned slots; optional gap/risk hints
└──────┬───────┘
       ▼
┌──────────────┐
│ 6. Decide    │  Keep / refine / discard / pin; add contingency;
│              │  inject task and re-enter at step 2 or 3
└──────────────┘
```

Each completed pass produces a **Mission Option** stored in the contingency pool. Progress is the quality of the **pinned top-three** plus credible contingencies for identified risks—not a single “plan complete” flag.

---

## 2. Top-three slots and contingency pool

```text
Contingency pool (many options, each with archetype + saved inputs)
        │ pin
   ┌────┼────┐
   ▼    ▼    ▼
  A     B     C     ← always-visible comparison set
```

### Default pinned trio

| Slot | Default archetype | Intent | Typical router bias |
|------|-------------------|--------|---------------------|
| **A** | `efficient` | Economy of force — cover tasks with least fuel/time | Direct-ish published-waypoint sequences; few extra vias |
| **B** | `synchronized` | Timed combined effects — TOT alignment, BDA after strike | Shared holds/IPs, timing windows; may accept longer legs |
| **C** | `maneuver` / unexpected axis (+ surprise) | Dislocate — non-obvious approach axis | Forced vias / corridor constraints (e.g. north then west entry vs direct from PSAB) |

Slots can be re-pinned to other archetypes (`shock`, `attrition`, hybrids). Historical rationale, objectives, and “gaps to hunt” for each archetype: **`docs/FORCE-APPROACHES.md`**.

### Contingencies beyond three

The pool may hold weather alternates, “corridor closed” branches, pure shock opening packages, resilience-heavy attrition plans, etc. Only three stay in continuous side-by-side comparison; the rest remain available to promote into a slot or to satisfy gap-assessment hints (“you have no resilient branch if C is denied”).

---

## 3. Saved router inputs and archetype (iterative planning)

Every Mission Option stores:

- **Approach archetype** (`efficient` | `synchronized` | `maneuver` | `surprise` | `shock` | `attrition` | hybrid tags)
- Task set and aircraft set
- Supplier id / mode
- Router parameters: vias, corridor/avoid polygons, timing windows, axis profile, sync group / BDA lag
- Human label and optional dislocation/deception hypothesis (especially for C)
- Timestamp; optional `parent_option_id` when refined from another option

Re-run with a patched input without rebuilding the world. Dynamic task insertion re-generates the affected aircraft inside the option being edited, preserving archetype and other inputs.

---

## 4. Comparison method

| Dimension | Efficient (A) | Synchronized (B) | Unexpected / maneuver (C) |
|-----------|---------------|------------------|---------------------------|
| Total distance / fuel | Primary | Secondary | Secondary |
| End-fuel margin | Required GO | Required GO | Required GO |
| Unallocated / unsatisfied tasks | Count + list | Count + list | Count + list |
| Timing alignment (TOT, BDA lag) | Weak | Primary | Weak |
| Approach-axis / corridor match | Weak | Weak | Primary |
| Archetype fit (does plan match its label?) | Yes | Yes | Yes |
| Qualitative notes / hypothesis | Free text | Free text | Free text |

Minimum viable comparison:

- Side-by-side: GO/NO-GO counts, total distance, unallocated count, archetype/emphasis label
- Pin/unpin into A/B/C
- Duplicate → patch one input → re-propagate

Later: archetype-aware **gap/risk/dependency** reports per `FORCE-APPROACHES.md` §5 (AI or rules). Human remains decision authority.

---

## 5. Relationship to civil vs mission route generation

- **Civil-style generation** supports **efficient** and as a base layer for others.
- **Mission route generation** adds vias, corridors, sync metadata, avoid regions for maneuver/synchronized/shock flavors.
- Fuel feasibility always stays in the **Route Propagation Service**.

See `docs/CIVIL-ROUTE-DEV-GUIDE.md`, `docs/MISSION-ROUTE-DEV-GUIDE.md`, `docs/SUPPLIER-ROUTE-TOOLS.md`, `docs/FORCE-APPROACHES.md`.

---

## 6. Progress tracking

A session is progressing when:

1. Pinned slots include GO routes for critical tasks, or
2. ≥2 options have been compared and a preference / next experiment recorded, or
3. Unallocated/unsatisfied tasks shrink across iterations, or
4. A dynamic insert was absorbed and re-validated, or
5. Identified gaps have a contingency in the pool or an explicit accept-risk note

Export to o-my-sim / UCI only for routes accepted from a chosen option.

---

## 7. Non-goals for the CONOPS prototype

- Fully automated selection of the “best” option
- Perfect multi-ship deconfliction or tanker planning
- Real-time re-planning under live threat tracks
- Replacing commander’s intent with archetype labels alone
- Encoding full doctrine or ROE
