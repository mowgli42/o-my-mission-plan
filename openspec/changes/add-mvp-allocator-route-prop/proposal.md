# Proposal: MVP Allocator + Route Generator + Propagation

## Why

Mission planning is inherently iterative. We need a minimal closed loop that lets a planner (or future automated process) “guess” an allocation and route, see whether the platforms can physically complete it (fuel), and then adjust.

## What

Deliver a working prototype that:

1. Loads a small demo world (Central/East Florida airbases + commercial navaids + sample ISR/strike tasks + 3–4 aircraft).
2. Simulates ATO ingestion by populating an unassigned task pool.
3. Performs simple regional task allocation to aircraft.
4. Generates an initial route for each assigned aircraft using navaid waypoints and the prescribed leg distances (≈80 nmi ISR, ≈20 nmi strike).
5. Exposes a FastAPI Route Propagation Service that tracks fuel remaining and burn rate per leg and answers feasibility.
6. Supports injection of one new task mid-route and re-propagation.

## Non-goals

- Full ATO schema parsing
- Advanced optimization, threats, weather, tankers, multi-ship coordination
- Production-grade UI (Swagger + optional later Svelte is enough)
- Real-time UCI bus integration (design the contracts; wire later)

## Success criteria

A developer can:
- Start the FastAPI service
- Load the demo world
- Run one full plan cycle (allocate → route → fuel check)
- Inject a new strike task and see the route + fuel state update
- See clear feasibility (GO / NO-GO) results
