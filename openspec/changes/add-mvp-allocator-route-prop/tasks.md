# Tasks — add-mvp-allocator-route-prop

## Phase 1 — Domain & Demo World
- [x] Define Pydantic models: Aircraft, Task, Airbase, Navaid, Leg, Route, FuelState, AllocationResult
- [x] Create Florida demo fixtures
  - 2 ISR + 3 fighters + 2 bombers (home bases, fuel, burn rate, reserve)
  - ≈4–5 ISR + 2–3 strike tasks
  - commercial navaids + airbases
- [x] Simple distance helper (haversine)

## Phase 2 — Allocator
- [x] Group tasks by crude geographic region
- [x] Assign groups to suitable aircraft (type preference + availability)
- [x] Always return both allocations **and** the list of unallocated tasks

## Phase 3 — Initial Route Generator
- [x] Build ordered waypoint list (home → navaids / proximity points → home)
- [x] Ensure aircraft comes within 80 nmi of each ISR task and within 20 nmi of each strike task
- [x] Legs may be any length; navaids used where helpful
- [x] Attach tasks to the appropriate points in the route

## Phase 4 — Route Propagation Service
- [x] FastAPI app with route create / get / propagate endpoints
- [x] Constant burn-rate model + fixed reserve
- [x] Per-leg remaining fuel + overall GO / NO-GO
- [x] Explicit “unexecutable due to fuel” flag

## Phase 5 — Dynamic Insertion
- [x] Endpoint to inject a new task
- [x] Full re-generation of the aircraft’s route + full fuel re-propagation
- [x] Return updated route + feasibility

## Phase 6 — Polish
- [x] Swagger examples / demo UI that shows unallocated tasks + fuel NO-GO cases
- [x] Unit tests for allocator, generator, fuel math, feedback
- [x] Dark-theme IxDF planning UI + README screenshots
- [ ] Update living OpenSpec after validation (archive change)
