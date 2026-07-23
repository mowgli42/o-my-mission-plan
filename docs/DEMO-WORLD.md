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

(Exact coordinates can be refined; these are sufficient for distance calculations.)

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

## Route construction rules (prototype)

- ISR / collection tasks → legs of approximately **80 nmi** between successive navaids / task points.
- Strike tasks → legs of approximately **20 nmi**.
- Every route starts and ends at the aircraft’s assigned home airbase.
- Tasks in the same geographic region are grouped and assigned to one aircraft when possible.

## Sample task pool (illustrative)

- ISR-01 … ISR-04 : collection tasks spread across Central / East FL
- STK-01 … STK-03 : strike tasks clustered near a target area

Exact coordinates and task definitions will live in fixtures once the allocator is implemented.
