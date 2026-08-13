"""Load fuzzy-reconciler region samples as fixed threats for the PSAB planner."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import LatLon, Task, TaskType, Threat
from .route_generator import PublishedFix

FIXED_THREAT_CATEGORIES = frozenset(
    {
        "sam_site",
        "surveillance_radar",
        "early_warning_radar",
        "ballistic_missile_site",
        "coastal_defense",
        "command_post",
        "elint_site",
    }
)

ROLE_BY_CATEGORY = {
    "sam_site": "SEAD",
    "surveillance_radar": "ISR",
    "early_warning_radar": "ISR",
    "elint_site": "ISR",
    "ballistic_missile_site": "STRIKE",
    "coastal_defense": "STRIKE",
    "command_post": "STRIKE",
}

PRIORITY_BY_CATEGORY = {
    "sam_site": 1,
    "ballistic_missile_site": 2,
    "early_warning_radar": 2,
    "command_post": 2,
    "elint_site": 3,
    "surveillance_radar": 3,
    "coastal_defense": 3,
}

KIND_BY_CATEGORY = {
    "sam_site": "SAM",
    "surveillance_radar": "SAM",
    "early_warning_radar": "SAM",
    "elint_site": "SAM",
    "ballistic_missile_site": "SAM",
    "coastal_defense": "AAA",
    "command_post": "SAM",
}

# UCI OrderOfBattle Record/Kind (docs/UCI-CONTRACTS.md hop 1b)
OOB_KIND_BY_CATEGORY = {
    "sam_site": "MissileRecord",
    "surveillance_radar": "EmitterRecord",
    "early_warning_radar": "EmitterRecord",
    "elint_site": "EmitterRecord",
    "ballistic_missile_site": "MissileRecord",
    "coastal_defense": "LandRecord",
    "command_post": "FacilityRecord",
}

EOB_RESERVED_KEYS = (
    "eob_record_id",
    "elnot",
    "be_number",
    "o_suffix",
    "site_pin",
    "evaluation_code",
    "country_code",
    "mobility",
    "operational_status",
)

SEVERITY_BY_STATUS = {
    "operational": "HIGH",
    "degraded": "MEDIUM",
    "standby": "MEDIUM",
    "offline": "LOW",
}


@dataclass
class FixedThreat:
    entity_id: str
    name: str
    latitude: float
    longitude: float
    category: str
    analyzed_at: str = ""
    range_km: float = 0.0
    band: str = ""
    status: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def preferred_role(self) -> str:
        return ROLE_BY_CATEGORY.get(self.category, "ISR")

    @property
    def priority(self) -> int:
        return PRIORITY_BY_CATEGORY.get(self.category, 4)


def default_fixture_path() -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures" / "regions" / "gulf_threats.json"


def sibling_fuzzy_reconciler_path(region: str = "gulf") -> Path:
    root = Path(__file__).resolve().parents[3]
    showcase = root / "fuzzy-reconciler" / "fixtures" / "regions" / "examples" / f"{region}_base.json"
    canonical = root / "fuzzy-reconciler" / "fixtures" / "regions" / "canonical" / f"{region}_base.json"
    if showcase.exists():
        return showcase
    return canonical


def resolve_region_path(region: str = "gulf", region_file: str | None = None, *, sibling: bool = False) -> Path:
    if region_file:
        return Path(region_file)
    if sibling:
        sibling_path = sibling_fuzzy_reconciler_path(region)
        if sibling_path.exists():
            return sibling_path
    bundled = default_fixture_path()
    if region != "gulf":
        sibling_path = sibling_fuzzy_reconciler_path(region)
        if sibling_path.exists():
            return sibling_path
    return bundled


def load_region_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if "entities" not in data:
        raise ValueError(f"{path} is not a fuzzy-reconciler region fixture (missing entities)")
    return data


def threats_from_region(
    data: dict[str, Any],
    *,
    max_threats: int | None = None,
    categories: set[str] | None = None,
) -> list[FixedThreat]:
    allowed = categories or set(FIXED_THREAT_CATEGORIES)
    threats: list[FixedThreat] = []
    for raw in data.get("entities", []):
        cat = str(raw.get("category") or raw.get("type") or "")
        if cat not in allowed:
            continue
        attrs = dict(raw.get("attributes") or {})
        threats.append(
            FixedThreat(
                entity_id=str(raw.get("id") or raw.get("entity_id") or ""),
                name=str(raw.get("name") or raw.get("id") or "unnamed"),
                latitude=float(raw.get("lat") or 0),
                longitude=float(raw.get("lon") or 0),
                category=cat,
                analyzed_at=str(raw.get("analyzed_at") or ""),
                range_km=float(attrs.get("range_km") or 0),
                band=str(attrs.get("band") or ""),
                status=str(attrs.get("status") or ""),
                attributes=attrs,
            )
        )
    threats.sort(key=lambda t: (t.priority, -t.range_km, t.entity_id))
    if max_threats is not None:
        threats = threats[: max(0, max_threats)]
    return threats


def to_demo_threat(fixed: FixedThreat) -> Threat:
    range_nmi = max(15.0, fixed.range_km * 0.54)
    return Threat(
        id=fixed.entity_id,
        kind=KIND_BY_CATEGORY.get(fixed.category, "SAM"),
        location=LatLon(lat=fixed.latitude, lon=fixed.longitude),
        severity=SEVERITY_BY_STATUS.get(fixed.status, "HIGH" if fixed.category == "sam_site" else "MEDIUM"),
        label=fixed.name,
        lethal_radius_nmi=min(range_nmi, 80.0),
        jam_radius_nmi=min(range_nmi * 2.5, 180.0),
    )


def to_task(fixed: FixedThreat) -> Task:
    role = fixed.preferred_role
    task_type = TaskType.ISR if role == "ISR" else TaskType.STRIKE
    prefix = "ISR" if task_type is TaskType.ISR else "STK"
    return Task(
        id=f"{prefix}-{fixed.entity_id}",
        type=task_type,
        location=LatLon(lat=fixed.latitude, lon=fixed.longitude),
        priority=max(1, 4 - fixed.priority),
        label=f"{role} {fixed.name}",
        target_entity_id=fixed.entity_id,
        target_type=fixed.category,
    )


def to_mission_fix(fixed: FixedThreat) -> PublishedFix:
    """Fixed OOB site as a published mission waypoint (not a runtime PROX point)."""
    return PublishedFix(
        id=f"FIX-{fixed.entity_id}",
        name=fixed.name,
        location=LatLon(lat=fixed.latitude, lon=fixed.longitude),
        kind="mission",
    )
