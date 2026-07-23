# Demo World — Central / East Florida

Lightweight planning area for the prototype. Real commercial navaids and realistic airbase locations.

## Airbases (home plates)

| ID | Name | Lat / Lon (approx) | Typical roles |
|----|------|--------------------|---------------|
| KXMR | Cape Canaveral / Patrick area | 28.47, -80.57 | ISR, fighter |
| KCOF | Patrick SFB | 28.23, -80.61 | ISR |
| KMLB | Melbourne Orlando Intl | 28.10, -80.65 | Mixed |
| KORL | Orlando Executive / nearby | 28.55, -81.33 | Fighter / bomber staging |
| KSRQ | Sarasota-Bradenton | 27.40, -82.55 | Secondary |

## Commercial Navaids used in routes

| ID | Name | Type | Approx location |
|----|------|------|-----------------|
| MLB | Melbourne | VOR/DME | East Central FL |
| ORL | Orlando | VORTAC | Central FL |
| LAL | Lakeland | VORTAC | Central FL |
| VRB | Vero Beach | VORTAC | East Central FL |
| OMN | Ormond Beach | VORTAC | Northeast FL |
| SRQ | Sarasota | VORTAC | Southwest FL |
| PIE | St Petersburg | VORTAC | Tampa Bay |
| PBI | Palm Beach | VORTAC | Southeast FL |
| CRG | Craig (Jacksonville) | VORTAC | Northeast FL |

## Aircraft inventory (prototype)

- 2 × ISR
- 3 × FIGHTER
- 2 × BOMBER

Each aircraft has:
- home airbase
- initial fuel quantity
- constant burn rate (fuel units per nmi)
- fixed reserve requirement

## Task pool (first planning cycle)

Approximately:
- 4–5 ISR / collection tasks
- 2–3 strike tasks

## Route construction rules

- The generated route is a sequence of **published waypoints only** (airbases, commercial navaids, optional fixed mission waypoints). See [`ROUTE-GENERATION.md`](ROUTE-GENERATION.md).
- After selection, validate that at least one published waypoint lies **within 80 nmi** of every assigned ISR task and **within 20 nmi** of every assigned strike task.
- Do **not** invent intermediate lat/lon points (`PROX-*`) at planning time.
- Legs are great-circle between consecutive published waypoints (any length).
- Every route starts and ends at the aircraft’s assigned home airbase.
- Assigned tasks that no published fix can cover are reported as unsatisfied.

## Feedback that must be visible

- List of tasks that remain unallocated after the allocation step.
- List of assigned tasks that no published waypoint can satisfy (proximity).
- GO / NO-GO for each route based on whether end-of-route fuel meets the fixed reserve.
