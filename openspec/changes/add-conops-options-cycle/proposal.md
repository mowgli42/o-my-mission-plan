# Proposal: CONOPS planning cycle + top-three Mission Options

## Why

Mission planning is iterative. A single route pass is not enough. The planner needs to keep multiple holistic options, compare them, and refine router inputs across cycles—especially to explore efficient routing, synchronized effects, and unexpected approach axes.

## What

- Document and implement a trackable planning cycle (ingest → frame → allocate → route → propagate → compare → decide).
- Persist **Mission Options** with full router inputs so passes can be re-run and compared.
- Support a **top-three** working set:
  - **A Efficient** — minimize distance/fuel while covering tasks
  - **B Synchronized** — timing intent for simultaneous/staggered strikes and post-strike BDA
  - **C Unexpected axis** — forced vias/corridor so approach is not the obvious radial from PSAB (e.g. north then west entry)
- Extend OpenSpec requirements and Gherkin to cover options, saved inputs, and comparison metrics.
- Keep civil/mission route suppliers behind the existing adapter model; fuel stays in the propagator.

## Non-goals

- Automated multi-objective solver that picks the single best option
- Full temporal multi-ship optimization in v1 (timing is stored and compared, not globally optimized)
- Live threat-driven replanning

## Success criteria

- Gherkin CONOPS scenarios are accepted as the behavioral contract
- Living OpenSpec includes Mission Option + comparison requirements
- API or in-memory session can create, pin (A/B/C), re-run, and compare options
- Router inputs round-trip with each option
