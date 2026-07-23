# Design: MVP Allocator + Route Generator + Propagation

## Key decisions

### 1. Demo world is first-class

A small, hard-coded (or fixture-driven) Central/East Florida world is part of the prototype. Real navaid identifiers and approximate coordinates give credibility without requiring a full GIS stack.

### 2. Leg distances are deliberate simplifications

- ISR tasks → target ~80 nmi between successive points
- Strike tasks → target ~20 nmi

This makes the generator trivial while still producing recognizably different routes for the two mission types.

### 3. Route Propagation is the only “live” service

Everything else (allocator, initial route builder) can be pure functions or short-lived endpoints. The propagator owns the mutable route + fuel state for each platform and is the natural place for later UCI publication of route updates.

### 4. Fuel model is intentionally crude

Constant burn rate per aircraft type (optionally scaled by a simple altitude/speed factor later). Reserves are a fixed percentage or absolute quantity. The important part is that feasibility is computed and visible, not that the numbers are aerodynamically perfect.

### 5. Dynamic insertion is “re-generate or simple splice”

For the prototype we can either:
- re-run the route generator with the new task added to the aircraft’s task list, or
- insert the new task at the geographically nearest point in the existing leg sequence.

Prefer the simpler of the two that still produces a usable fuel check.

## Risks

- Over-engineering the allocator or route generator before the propagator is solid.
- Spending time on pretty maps before the core feasibility loop works.

## Mitigation

Build in this order:
1. Domain models + demo fixtures
2. Allocator (pure)
3. Route generator (pure)
4. Propagator FastAPI + fuel math
5. Dynamic insert endpoint
6. Only then optional map UI
