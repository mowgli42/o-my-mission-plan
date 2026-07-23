"""Gulf War demo world — Coalition launch from PSAB (Prince Sultan AB).

Aircraft launch from OEPS / PSAB (Al Kharj, Saudi Arabia). Collection and
strike tasks sit across Kuwait and Iraq. Published navigation database =
airbases + commercial navaids + fixed mission waypoints (not invented at
planning time). See docs/DEMO-WORLD.md and docs/ROUTE-GENERATION.md.
"""

from __future__ import annotations

from .models import (
    Airbase,
    Aircraft,
    AircraftType,
    LatLon,
    Navaid,
    Task,
    TaskType,
    Threat,
)
from .route_generator import PublishedFix

SCENARIO_ID = "gulf-war-psab-001"
SCENARIO_NAME = "Desert Storm — PSAB launch (Kuwait / Iraq)"
LAUNCH_BASE_ID = "OEPS"

# ---------------------------------------------------------------------------
# Airbases (launch + published recovery / theater plates)
# ---------------------------------------------------------------------------

AIRBASES: dict[str, Airbase] = {
    "OEPS": Airbase(
        id="OEPS",
        name="Prince Sultan AB (PSAB) / Al Kharj",
        location=LatLon(lat=24.0627, lon=47.5805),
    ),
    "OEDR": Airbase(
        id="OEDR",
        name="King Abdulaziz AB / Dhahran",
        location=LatLon(lat=26.2654, lon=50.1520),
    ),
    "OKBK": Airbase(
        id="OKBK",
        name="Kuwait International",
        location=LatLon(lat=29.2266, lon=47.9689),
    ),
    "ORBI": Airbase(
        id="ORBI",
        name="Baghdad International (published fix)",
        location=LatLon(lat=33.2625, lon=44.2344),
    ),
}

# ---------------------------------------------------------------------------
# Commercial / published navaids (approx; demo fidelity)
# ---------------------------------------------------------------------------

NAVAIDS: dict[str, Navaid] = {
    "PSA": Navaid(
        id="PSA",
        name="Prince Sultan",
        location=LatLon(lat=24.0750, lon=47.5850),
        navaid_type="VORTAC",
    ),
    "HFR": Navaid(
        id="HFR",
        name="Hofuf / Al Ahsa",
        location=LatLon(lat=25.2853, lon=49.4852),
        navaid_type="VORTAC",
    ),
    "DHA": Navaid(
        id="DHA",
        name="Dhahran",
        location=LatLon(lat=26.2650, lon=50.1500),
        navaid_type="VORTAC",
    ),
    "BAH": Navaid(
        id="BAH",
        name="Bahrain",
        location=LatLon(lat=26.2708, lon=50.6336),
        navaid_type="VORTAC",
    ),
    "KWI": Navaid(
        id="KWI",
        name="Kuwait",
        location=LatLon(lat=29.2400, lon=47.9700),
        navaid_type="VOR/DME",
    ),
    "RAS": Navaid(
        id="RAS",
        name="Ras Al Khafji area",
        location=LatLon(lat=28.4200, lon=48.5000),
        navaid_type="VOR",
    ),
}

# ---------------------------------------------------------------------------
# Fixed mission waypoints (part of the published nav database — not runtime)
# ---------------------------------------------------------------------------

MISSION_WAYPOINTS: dict[str, PublishedFix] = {
    "MW-MUTLA": PublishedFix(
        id="MW-MUTLA",
        name="Mutla Ridge (Kuwait north)",
        location=LatLon(lat=29.5500, lon=47.7000),
        kind="mission",
    ),
    "MW-KUWAIT-CITY": PublishedFix(
        id="MW-KUWAIT-CITY",
        name="Kuwait City approaches",
        location=LatLon(lat=29.3500, lon=47.9500),
        kind="mission",
    ),
    "MW-BASRA": PublishedFix(
        id="MW-BASRA",
        name="Basra approaches",
        location=LatLon(lat=30.5000, lon=47.7800),
        kind="mission",
    ),
    "MW-NASIRIYAH": PublishedFix(
        id="MW-NASIRIYAH",
        name="Nasiriyah area",
        location=LatLon(lat=31.0500, lon=46.2600),
        kind="mission",
    ),
    "MW-TALIL": PublishedFix(
        id="MW-TALIL",
        name="Talil / southern MSR",
        location=LatLon(lat=30.9400, lon=46.0900),
        kind="mission",
    ),
    "MW-BAGHDAD-S": PublishedFix(
        id="MW-BAGHDAD-S",
        name="Baghdad south",
        location=LatLon(lat=33.1000, lon=44.4000),
        kind="mission",
    ),
    "MW-WADI-AL-BATIN": PublishedFix(
        id="MW-WADI-AL-BATIN",
        name="Wadi al-Batin corridor",
        location=LatLon(lat=29.9000, lon=46.5000),
        kind="mission",
    ),
}

# ---------------------------------------------------------------------------
# Aircraft — all launch from PSAB (OEPS)
# Fuel sized for Gulf theater round-trips (prototype units).
# ---------------------------------------------------------------------------

AIRCRAFT: list[Aircraft] = [
    Aircraft(
        id="ISR-1",
        type=AircraftType.ISR,
        home_base_id="OEPS",
        initial_fuel=24000.0,
        burn_rate_per_nmi=8.0,
        reserve_fuel=3000.0,
        label="Rivet-1 (ISR)",
        weapons_loadout=0,
    ),
    Aircraft(
        id="ISR-2",
        type=AircraftType.ISR,
        home_base_id="OEPS",
        initial_fuel=22000.0,
        burn_rate_per_nmi=7.5,
        reserve_fuel=2800.0,
        label="Rivet-2 (ISR)",
        weapons_loadout=0,
    ),
    Aircraft(
        id="FTR-1",
        type=AircraftType.FIGHTER,
        home_base_id="OEPS",
        initial_fuel=20000.0,
        burn_rate_per_nmi=12.0,
        reserve_fuel=2500.0,
        label="Viper-1",
        weapons_loadout=4,
    ),
    Aircraft(
        id="FTR-2",
        type=AircraftType.FIGHTER,
        home_base_id="OEPS",
        initial_fuel=20000.0,
        burn_rate_per_nmi=12.5,
        reserve_fuel=2500.0,
        label="Viper-2",
        weapons_loadout=4,
    ),
    Aircraft(
        id="FTR-3",
        type=AircraftType.FIGHTER,
        home_base_id="OEPS",
        initial_fuel=19000.0,
        burn_rate_per_nmi=11.8,
        reserve_fuel=2400.0,
        label="Viper-3",
        weapons_loadout=4,
    ),
    Aircraft(
        id="BMB-1",
        type=AircraftType.BOMBER,
        home_base_id="OEPS",
        initial_fuel=40000.0,
        burn_rate_per_nmi=18.0,
        reserve_fuel=5000.0,
        label="Buff-1",
        weapons_loadout=12,
    ),
    Aircraft(
        id="BMB-2",
        type=AircraftType.BOMBER,
        home_base_id="OEPS",
        initial_fuel=38000.0,
        burn_rate_per_nmi=17.0,
        reserve_fuel=4800.0,
        label="Buff-2",
        weapons_loadout=12,
    ),
]

# ---------------------------------------------------------------------------
# Unassigned task pool — Kuwait & Iraq
# ---------------------------------------------------------------------------

TASKS: list[Task] = [
    Task(
        id="ISR-01",
        type=TaskType.ISR,
        location=LatLon(lat=29.40, lon=47.90),
        priority=2,
        label="Collect Kuwait City / coastal corridor",
    ),
    Task(
        id="ISR-02",
        type=TaskType.ISR,
        location=LatLon(lat=30.45, lon=47.70),
        priority=2,
        label="Collect Basra approaches",
    ),
    Task(
        id="ISR-03",
        type=TaskType.ISR,
        location=LatLon(lat=31.00, lon=46.20),
        priority=1,
        label="Collect Nasiriyah / southern MSR",
    ),
    Task(
        id="ISR-04",
        type=TaskType.ISR,
        location=LatLon(lat=33.20, lon=44.40),
        priority=2,
        label="Collect Baghdad area",
    ),
    Task(
        id="ISR-05",
        type=TaskType.ISR,
        location=LatLon(lat=29.80, lon=46.60),
        priority=1,
        label="Collect Wadi al-Batin corridor",
    ),
    Task(
        id="STK-01",
        type=TaskType.STRIKE,
        location=LatLon(lat=29.52, lon=47.68),
        priority=3,
        label="Strike Mutla Ridge area",
    ),
    Task(
        id="STK-02",
        type=TaskType.STRIKE,
        location=LatLon(lat=30.48, lon=47.75),
        priority=3,
        label="Strike Basra area target",
    ),
    Task(
        id="STK-03",
        type=TaskType.STRIKE,
        location=LatLon(lat=33.05, lon=44.42),
        priority=2,
        label="Strike Baghdad south target",
    ),
]

# ---------------------------------------------------------------------------
# Demo threats (battlespace-style route impact — not inventing route geometry)
# ---------------------------------------------------------------------------

THREATS: list[Threat] = [
    Threat(
        id="THREAT-SAM-01",
        kind="SAM",
        location=LatLon(lat=29.78, lon=47.55),
        severity="HIGH",
        label="Kuwait north SAM battery",
        lethal_radius_nmi=45.0,
        jam_radius_nmi=140.0,
    ),
    Threat(
        id="THREAT-AAA-02",
        kind="AAA",
        location=LatLon(lat=30.55, lon=47.65),
        severity="MEDIUM",
        label="Basra AAA umbrella",
        lethal_radius_nmi=25.0,
        jam_radius_nmi=80.0,
    ),
    Threat(
        id="THREAT-SAM-03",
        kind="SAM",
        location=LatLon(lat=32.95, lon=44.55),
        severity="CRITICAL",
        label="Baghdad south SAM",
        lethal_radius_nmi=55.0,
        jam_radius_nmi=160.0,
    ),
    Threat(
        id="THREAT-INT-04",
        kind="FIGHTER",
        location=LatLon(lat=28.80, lon=47.20),
        severity="MEDIUM",
        label="CAP intercept corridor",
        lethal_radius_nmi=30.0,
        jam_radius_nmi=100.0,
    ),
]


def get_airbase(aircraft: Aircraft) -> Airbase:
    return AIRBASES[aircraft.home_base_id]
