# Proposal: MVP Allocator + Route Generator + Propagation

## Why

Mission planning is inherently iterative. We need a minimal closed loop that lets a planner (or future automated process) “guess” an allocation and route, see whether the platforms can physically complete it (fuel), and then adjust.

## What

Deliver a working prototype that:

1. Loads a small demo world (Central/East Florida airbases + commercial navaids + sample tasks + **2 ISR, 3 fighters, 2 bombers**).
2. Simulates ATO ingestion by populating an unassigned task pool (≈4–5 ISR + 2–3 strike).
3. Performs simple regional task allocation to aircraft and **explicitly reports any unallocated tasks**.
4. Generates an initial route for each assigned aircraft using commercial navaid waypoints. The route only needs to bring the aircraft **within 80 nmi of each ISR task** and **within 20 nmi of each strike task**. Legs may be any length required.
5. Exposes a FastAPI Route Propagation Service that tracks fuel remaining (constant burn rate) + fixed reserve and answers feasibility. **Clearly flags routes that are unexecutable due to fuel constraints**.
6. Supports injection of one new task by **fully re-generating / re-assessing** the route and re-propagating fuel.

## Non-goals

- Full ATO schema parsing
- Advanced optimization, threats, weather, tankers, multi-ship coordination
- Priority-based allocation algorithms (report unallocated only)
- Production-grade UI (Swagger is enough for first prototype)
- Real-time UCI bus integration (design the contracts; wire later)

## Success criteria

A developer can:
- Start the FastAPI service
- Load the demo world
- Run one full plan cycle (allocate → route → fuel check)
- See which tasks (if any) were left unallocated
- See GO / NO-GO (fuel) results for every route
- Inject a new strike task, force full re-assessment, and see the updated feasibility
