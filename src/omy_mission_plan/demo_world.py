"""Central / East Florida demo world for the mission-planning prototype."""

from __future__ import annotations

from .models import (
    Airbase,
    Aircraft,
    AircraftType,
    LatLon,
    Navaid,
    Task,
    TaskType,
)

# ---------------------------------------------------------------------------
# Airbases
# ---------------------------------------------------------------------------

AIRBASES: dict[str, Airbase] = {
    "KXMR": Airbase(
        id="KXMR",
        name="Cape Canaveral / Patrick area",
        location=LatLon(lat=28.47, lon=-80.57),
    ),
    "KCOF": Airbase(
        id="KCOF",
        name="Patrick SFB",
        location=LatLon(lat=28.23, lon=-80.61),
    ),
    "KMLB": Airbase(
        id="KMLB",
        name="Melbourne Orlando Intl",
        location=LatLon(lat=28.10, lon=-80.65),
    ),
    "KORL": Airbase(
        id="KORL",
        name="Orlando Executive area",
        location=LatLon(lat=28.55, lon=-81.33),
    ),
    "KSRQ": Airbase(
        id="KSRQ",
        name="Sarasota-Bradenton",
        location=LatLon(lat=27.40, lon=-82.55),
    ),
}

# ---------------------------------------------------------------------------
# Commercial navaids
# ---------------------------------------------------------------------------

NAVAIDS: dict[str, Navaid] = {
    "MLB": Navaid(id="MLB", name="Melbourne", location=LatLon(lat=28.10, lon=-80.63), navaid_type="VOR/DME"),
    "ORL": Navaid(id="ORL", name="Orlando", location=LatLon(lat=28.55, lon=-81.33), navaid_type="VORTAC"),
    "LAL": Navaid(id="LAL", name="Lakeland", location=LatLon(lat=27.99, lon=-82.01), navaid_type="VORTAC"),
    "VRB": Navaid(id="VRB", name="Vero Beach", location=LatLon(lat=27.66, lon=-80.42), navaid_type="VORTAC"),
    "OMN": Navaid(id="OMN", name="Ormond Beach", location=LatLon(lat=29.30, lon=-81.11), navaid_type="VORTAC"),
    "SRQ": Navaid(id="SRQ", name="Sarasota", location=LatLon(lat=27.40, lon=-82.55), navaid_type="VORTAC"),
    "PIE": Navaid(id="PIE", name="St Petersburg", location=LatLon(lat=27.91, lon=-82.68), navaid_type="VORTAC"),
    "PBI": Navaid(id="PBI", name="Palm Beach", location=LatLon(lat=26.68, lon=-80.09), navaid_type="VORTAC"),
    "CRG": Navaid(id="CRG", name="Craig", location=LatLon(lat=30.34, lon=-81.51), navaid_type="VORTAC"),
}

# ---------------------------------------------------------------------------
# Aircraft (2 ISR, 3 fighters, 2 bombers)
# Fuel units are arbitrary but consistent (think “hundreds of pounds”).
# ---------------------------------------------------------------------------

AIRCRAFT: list[Aircraft] = [
    # ISR
    Aircraft(
        id="ISR-1",
        type=AircraftType.ISR,
        home_base_id="KCOF",
        initial_fuel=12000.0,
        burn_rate_per_nmi=8.0,
        reserve_fuel=2000.0,
        label="Hawk-1 (ISR)",
    ),
    Aircraft(
        id="ISR-2",
        type=AircraftType.ISR,
        home_base_id="KXMR",
        initial_fuel=11000.0,
        burn_rate_per_nmi=7.5,
        reserve_fuel=1800.0,
        label="Hawk-2 (ISR)",
    ),
    # Fighters
    Aircraft(
        id="FTR-1",
        type=AircraftType.FIGHTER,
        home_base_id="KMLB",
        initial_fuel=9000.0,
        burn_rate_per_nmi=12.0,
        reserve_fuel=1500.0,
        label="Viper-1",
    ),
    Aircraft(
        id="FTR-2",
        type=AircraftType.FIGHTER,
        home_base_id="KORL",
        initial_fuel=9500.0,
        burn_rate_per_nmi=12.5,
        reserve_fuel=1600.0,
        label="Viper-2",
    ),
    Aircraft(
        id="FTR-3",
        type=AircraftType.FIGHTER,
        home_base_id="KMLB",
        initial_fuel=8800.0,
        burn_rate_per_nmi=11.8,
        reserve_fuel=1500.0,
        label="Viper-3",
    ),
    # Bombers
    Aircraft(
        id="BMB-1",
        type=AircraftType.BOMBER,
        home_base_id="KORL",
        initial_fuel=22000.0,
        burn_rate_per_nmi=18.0,
        reserve_fuel=3500.0,
        label="Bone-1",
    ),
    Aircraft(
        id="BMB-2",
        type=AircraftType.BOMBER,
        home_base_id="KSRQ",
        initial_fuel=20000.0,
        burn_rate_per_nmi=17.0,
        reserve_fuel=3200.0,
        label="Bone-2",
    ),
]

# ---------------------------------------------------------------------------
# Unassigned task pool (first planning cycle)
# ---------------------------------------------------------------------------

TASKS: list[Task] = [
    # ISR / collection
    Task(id="ISR-01", type=TaskType.ISR, location=LatLon(lat=28.40, lon=-80.70), priority=2, label="Collect Cape area"),
    Task(id="ISR-02", type=TaskType.ISR, location=LatLon(lat=28.00, lon=-81.20), priority=1, label="Collect Central FL"),
    Task(id="ISR-03", type=TaskType.ISR, location=LatLon(lat=27.70, lon=-80.50), priority=2, label="Collect Vero corridor"),
    Task(id="ISR-04", type=TaskType.ISR, location=LatLon(lat=29.10, lon=-81.00), priority=1, label="Collect North of OMN"),
    Task(id="ISR-05", type=TaskType.ISR, location=LatLon(lat=27.50, lon=-82.40), priority=1, label="Collect Sarasota approaches"),
    # Strike
    Task(id="STK-01", type=TaskType.STRIKE, location=LatLon(lat=28.20, lon=-81.00), priority=3, label="Strike target Alpha"),
    Task(id="STK-02", type=TaskType.STRIKE, location=LatLon(lat=27.80, lon=-80.60), priority=3, label="Strike target Bravo"),
    Task(id="STK-03", type=TaskType.STRIKE, location=LatLon(lat=28.60, lon=-81.40), priority=2, label="Strike target Charlie"),
]


def get_airbase(aircraft: Aircraft) -> Airbase:
    return AIRBASES[aircraft.home_base_id]
