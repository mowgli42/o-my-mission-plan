"""Export final planned routes for o-my-sim import / launch publish.

Contract documented in docs/OMY-SIM-ROUTES.md.
Schema id: o-my.mission-plan.routes/v1
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from . import demo_world
from .models import Aircraft, FuelState, Route

SCHEMA_ID = "o-my.mission-plan.routes/v1"
UCI_TOPIC = "uci.route"
DEFAULT_EXPORT_DIR = Path("data/routes")


def _waypoint_dict(wp, seq: int) -> dict[str, Any]:
    return {
        "seq": seq,
        "id": wp.id,
        "name": wp.name,
        "kind": wp.kind,
        "lat": wp.location.lat,
        "lon": wp.location.lon,
        "associated_task_id": wp.associated_task_id,
    }


def _leg_dict(leg, seq: int) -> dict[str, Any]:
    return {
        "seq": seq,
        "from_id": leg.from_waypoint.id,
        "to_id": leg.to_waypoint.id,
        "distance_nmi": leg.distance_nmi,
        "fuel_burn": leg.fuel_burn,
        "fuel_remaining_after": leg.fuel_remaining_after,
    }


def route_record(
    planned: Any,
    aircraft: Aircraft,
    *,
    include_nogo: bool = False,
) -> Optional[dict[str, Any]]:
    """Build one aircraft route record for the export bundle."""
    if planned.route is None:
        return None
    if planned.status == "idle":
        return None
    if planned.status == "NO-GO" and not include_nogo:
        return None

    route: Route = planned.route
    fuel: Optional[FuelState] = planned.fuel

    return {
        "aircraft_id": planned.aircraft_id,
        "callsign": planned.label or planned.aircraft_id,
        "aircraft_type": planned.aircraft_type,
        "home_base_id": planned.home_base_id,
        "uci_topic": UCI_TOPIC,
        "launch": {
            "when": "on_aircraft_launch",
            "publish": planned.status == "GO",
            "launch_base_id": demo_world.LAUNCH_BASE_ID,
        },
        "status": planned.status,
        "assigned_task_ids": list(planned.assigned_task_ids),
        "unsatisfied_task_ids": list(planned.unsatisfied_task_ids),
        "waypoints": [_waypoint_dict(wp, i) for i, wp in enumerate(route.waypoints)],
        "legs": [_leg_dict(leg, i) for i, leg in enumerate(route.legs)],
        "total_distance_nmi": route.total_distance_nmi,
        "feasibility": {
            "go": bool(route.feasible),
            "initial_fuel": aircraft.initial_fuel,
            "reserve_fuel": aircraft.reserve_fuel,
            "burn_rate_per_nmi": aircraft.burn_rate_per_nmi,
            "final_fuel": fuel.final_fuel if fuel else None,
            "infeasible_reason": route.infeasible_reason,
        },
    }


def build_export_bundle(
    plan: Any,
    aircraft: list[Aircraft],
    *,
    include_nogo: bool = False,
    scenario_id: str = demo_world.SCENARIO_ID,
) -> dict[str, Any]:
    """Assemble the o-my-sim import document from a completed plan cycle."""
    by_id = {a.id: a for a in aircraft}
    routes: list[dict[str, Any]] = []
    for planned in plan.plans:
        ac = by_id.get(planned.aircraft_id)
        if ac is None:
            continue
        rec = route_record(planned, ac, include_nogo=include_nogo)
        if rec is not None:
            routes.append(rec)

    return {
        "schema": SCHEMA_ID,
        "scenario_id": scenario_id,
        "scenario_name": demo_world.SCENARIO_NAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "launch_base_id": demo_world.LAUNCH_BASE_ID,
        "uci": {
            "route_topic": UCI_TOPIC,
            "notes": (
                "o-my-sim loads this file and publishes each GO route on "
                f"{UCI_TOPIC} when the corresponding aircraft launches."
            ),
        },
        "summary": {
            "route_count": len(routes),
            "go": sum(1 for r in routes if r["status"] == "GO"),
            "nogo": sum(1 for r in routes if r["status"] == "NO-GO"),
            "plan_summary": dict(plan.summary),
            "unallocated_task_ids": list(plan.allocation.unallocated_task_ids),
        },
        "routes": routes,
    }


def write_export_bundle(
    bundle: dict[str, Any],
    directory: Path | str = DEFAULT_EXPORT_DIR,
    *,
    also_per_aircraft: bool = True,
) -> dict[str, str]:
    """
    Write the bundle JSON (and optional per-aircraft files).

    Returns a map of logical name → path written.
    """
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    scenario = bundle["scenario_id"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_name = f"{scenario}-routes-{stamp}.json"
    bundle_path = out_dir / bundle_name
    bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    written["bundle"] = str(bundle_path)

    latest = out_dir / f"{scenario}-routes-latest.json"
    latest.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    written["latest"] = str(latest)

    if also_per_aircraft:
        ac_dir = out_dir / "aircraft"
        ac_dir.mkdir(parents=True, exist_ok=True)
        for route in bundle["routes"]:
            aid = route["aircraft_id"]
            path = ac_dir / f"{aid}.json"
            path.write_text(json.dumps(route, indent=2) + "\n", encoding="utf-8")
            written[aid] = str(path)

    return written
