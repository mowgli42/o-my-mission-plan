# Design: MVP Allocator + Route Generator + Propagation

## Key decisions

### 1. Demo world is first-class

A small, fixture-driven Central/East Florida world is part of the prototype. Real navaid identifiers and approximate coordinates give credibility without a full GIS stack.

Aircraft inventory (fixed for demo):
- 2 × ISR
- 3 × FIGHTER
- 2 × BOMBER

Task pool (first cycle): ≈4–5 ISR + 2–3 strike.

### 2. Proximity, not fixed leg length

The route only needs to get the aircraft **within**:
- 80 nmi of an ISR / collection task
- 20 nmi of a strike task

Individual legs may be as long as needed to connect home base → navaids → task proximity points → home. This is simpler and more realistic than forcing every leg to be exactly 80/20 nmi.

### 3. Route Propagation is the only “live” service

Everything else (allocator, initial route builder) can be pure functions or short-lived endpoints. The propagator owns the mutable route + fuel state for each platform and is the natural place for later UCI publication of route updates.

### 4. Fuel model is deliberately crude

- Constant burn rate (fuel units per nmi) per aircraft type
- Fixed reserve (absolute quantity or percentage of initial fuel)
- Feasibility = remaining fuel at end of route ≥ reserve → GO, else NO-GO / unexecutable

The important part is that the constraint is visible and actionable.

### 5. Dynamic insertion = full re-assessment

When a new task appears, the entire route for that aircraft is re-generated with the new task included and fuel is fully re-propagated. No attempt at mid-route splicing in the prototype.

### 6. Explicit feedback is required

- Allocation results always include the list of tasks that could not be assigned.
- Feasibility results clearly state when a route violates the fuel reserve constraint.

(Priority handling is a future extension; for now we only surface unallocated tasks.)

## Risks

- Over-engineering the allocator or route generator before the propagator is solid.
- Spending time on maps before the core feasibility + feedback loop works.

## Mitigation / build order

1. Domain models + demo fixtures (2 ISR / 3 FTR / 2 BMB + tasks + navaids)
2. Allocator (pure) + unallocated-task reporting
3. Route generator (proximity-based, pure)
4. Propagator FastAPI + constant-burn fuel math + GO/NO-GO
5. Dynamic insert = full re-generate + re-propagate
6. Only then optional map UI
