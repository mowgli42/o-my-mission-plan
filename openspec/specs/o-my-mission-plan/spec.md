# o-my-mission-plan

## Purpose

Enable iterative “guess-and-see” mission planning cycles for the o-my OMS ecosystem.

The system:
- Accepts (or simulates) a set of unassigned ISR/collection and strike tasks (proxy for ATO ingestion).
- Allocates groups of tasks in a geographic region to suitable aircraft resources (ISR, fighter, or bomber) that have an assigned takeoff/landing airbase.
- Generates an initial route for each assigned aircraft that starts and ends at its home airbase and visits the tasks using commercial navaid points, with characteristic leg lengths (~80 nmi ISR, ~20 nmi strike).
- Provides a Route Propagation Service that tracks fuel remaining and burn rate for each leg and answers whether the platform can safely complete the remaining route.
- Supports insertion of a newly identified task during execution and re-propagation of the route + fuel state.

Richer planning services (full ATO parsing, advanced allocation, loadout determination, optimization, threat avoidance) are out of scope for this capability and will be supplied externally via UCI messages.

## Requirements

### R1 — Unassigned Task Pool

The system SHALL maintain a pool of unassigned tasks.

Each task SHALL have at minimum:
- unique identifier
- type: `ISR` | `STRIKE`
- geographic location (lat/lon or associated navaid)
- optional priority / time window (may be stubbed in prototype)

### R2 — Aircraft Resources

The system SHALL maintain a set of aircraft resources.

Each aircraft SHALL have at minimum:
- unique identifier
- type: `ISR` | `FIGHTER` | `BOMBER`
- home airbase (identifier + lat/lon)
- initial fuel quantity and burn-rate model parameters

### R3 — Simple Regional Task Allocation

The system SHALL provide a simple allocator that:
- Groups tasks that fall in the same geographic region
- Assigns a group to a suitable aircraft (matching capability type when possible)
- Leaves residual tasks unassigned if no suitable aircraft remains

### R4 — Initial Route Generator

Given an aircraft and its assigned tasks, the system SHALL generate an ordered route that:
- Starts at the aircraft’s home airbase
- Visits the assigned tasks using commercial navaid points as intermediate waypoints where needed
- Uses approximately 80 nmi legs for ISR tasks and approximately 20 nmi legs for strike tasks
- Ends at the aircraft’s home airbase

### R5 — Route Propagation Service (Fuel & Feasibility)

The system SHALL expose a FastAPI service that, for a given route:
- Tracks remaining fuel after each leg using a simple burn-rate model
- Reports overall feasibility (can the platform complete the route with required reserves?)
- Supports stepping / advancing the route (fuel burn simulation)

### R6 — Dynamic Task Insertion

During a live route, the system SHALL accept a newly identified task, re-insert it into the route (simple insertion or re-generation), and re-propagate fuel state, returning an updated feasibility result.

### R7 — UCI-Oriented Contracts

Public interfaces (task, aircraft status, route, allocation results) SHALL be designed so they can later be published/consumed as UCI-aligned messages without changing the core domain model.

## Non-goals (prototype)

- Full ATO XML/JSON parsing
- Sophisticated multi-criteria optimization or threat avoidance
- Tanker / aerial refueling modeling
- Multi-ship deconfliction or formation routing
- Detailed loadout / weapons employment calculation
- Weather, airspace restrictions, or NOTAMs
