# Demo World — Gulf War / PSAB launch

Coalition aircraft launch from **Prince Sultan Air Base (PSAB / OEPS)** at Al Kharj,
Saudi Arabia. Collection and strike tasks span **Kuwait and Iraq**.

Scenario id: `gulf-war-psab-001`

## Launch base

| ID | Name | Lat / Lon (approx) | Role |
|----|------|--------------------|------|
| OEPS | Prince Sultan AB (PSAB) | 24.06, 47.58 | **Home plate for all demo aircraft** |

## Other published airbases (nav database)

| ID | Name | Lat / Lon (approx) |
|----|------|--------------------|
| OEDR | King Abdulaziz AB / Dhahran | 26.27, 50.15 |
| OKBK | Kuwait International | 29.23, 47.97 |
| ORBI | Baghdad International (published fix) | 33.26, 44.23 |

## Commercial navaids

| ID | Name | Type | Approx location |
|----|------|------|-----------------|
| PSA | Prince Sultan | VORTAC | PSAB |
| HFR | Hofuf / Al Ahsa | VORTAC | Eastern SA |
| DHA | Dhahran | VORTAC | Eastern SA |
| BAH | Bahrain | VORTAC | Bahrain |
| KWI | Kuwait | VOR/DME | Kuwait |
| RAS | Ras Al Khafji area | VOR | SA–Kuwait border |

## Fixed mission waypoints (published — not invented at runtime)

| ID | Name | Approx location |
|----|------|-----------------|
| MW-MUTLA | Mutla Ridge (Kuwait north) | 29.55, 47.70 |
| MW-KUWAIT-CITY | Kuwait City approaches | 29.35, 47.95 |
| MW-BASRA | Basra approaches | 30.50, 47.78 |
| MW-NASIRIYAH | Nasiriyah area | 31.05, 46.26 |
| MW-TALIL | Talil / southern MSR | 30.94, 46.09 |
| MW-BAGHDAD-S | Baghdad south | 33.10, 44.40 |
| MW-WADI-AL-BATIN | Wadi al-Batin corridor | 29.90, 46.50 |

## Aircraft inventory (all home = OEPS)

- 2 × ISR (Rivet-1 / Rivet-2)
- 3 × FIGHTER (Viper-1..3)
- 2 × BOMBER (Buff-1 / Buff-2)

Fuel loads are sized for Gulf theater round-trips (prototype units).

## Task pool (first planning cycle)

ISR / collection across Kuwait City, Basra, Nasiriyah, Baghdad, Wadi al-Batin.  
Strike at Mutla Ridge, Basra area, Baghdad south.

## Route construction rules

- Published waypoints only (airbases + navaids + fixed mission waypoints). See [`ROUTE-GENERATION.md`](ROUTE-GENERATION.md).
- Proximity success: within **80 nmi** of ISR tasks, **20 nmi** of strike tasks.
- Every route starts and ends at **OEPS (PSAB)**.
- Final GO routes are exported for **o-my-sim** — see [`OMY-SIM-ROUTES.md`](OMY-SIM-ROUTES.md).

## Feedback that must be visible

- Unallocated tasks after allocation
- Assigned tasks with no published fix in range
- GO / NO-GO fuel feasibility per route
