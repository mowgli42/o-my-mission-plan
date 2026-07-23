"""Routes overview enrichment for battlespace / debrief-aligned UI.

Builds top-line metrics, per-route threat impact (battlespace bands), and
end-to-end timeline / key events (o-my-debrief style) from a plan cycle.
"""

from __future__ import annotations

from typing import Any, Optional

from .geo import haversine_nmi
from .models import Aircraft, LatLon, Route, Task, TaskType, Threat, Waypoint
from .planning import PlanCycleResult, PlannedAircraft

# Battlespace-manager band thresholds (nm)
BAND_STRIKE_NM = 50.0
BAND_EJ_NM = 100.0
BAND_JAM_NM = 160.0

# Assumed cruise for timeline ETA stubs (prototype)
CRUISE_KT = 420.0


def band_for_distance(nm: float) -> str:
    if nm <= BAND_STRIKE_NM:
        return "STRIKE"
    if nm <= BAND_EJ_NM:
        return "EJ"
    if nm <= BAND_JAM_NM:
        return "JAM"
    return "OUT"


def band_color(band: str) -> str:
    return {
        "STRIKE": "#ef4444",
        "EJ": "#f97316",
        "JAM": "#a78bfa",
        "OUT": "#64748b",
    }.get(band, "#64748b")


def _segment_closest_nm(a: LatLon, b: LatLon, threat: LatLon, samples: int = 8) -> float:
    best = float("inf")
    for i in range(samples + 1):
        t = i / samples
        lat = a.lat + (b.lat - a.lat) * t
        lon = a.lon + (b.lon - a.lon) * t
        best = min(best, haversine_nmi(LatLon(lat=lat, lon=lon), threat))
    return best


def build_impact_segments(
    waypoints: list[Waypoint],
    threat: Threat,
) -> dict[str, Any]:
    segments = []
    cumulative = [0.0]
    closest_index = 0
    closest_nm = float("inf")

    for i in range(len(waypoints) - 1):
        a, b = waypoints[i], waypoints[i + 1]
        length = haversine_nmi(a.location, b.location)
        cumulative.append(cumulative[-1] + length)
        dist = _segment_closest_nm(a.location, b.location, threat.location)
        band = band_for_distance(dist) if dist <= BAND_JAM_NM else "OUT"
        if dist < closest_nm:
            closest_nm = dist
            closest_index = i
        segments.append(
            {
                "index": i,
                "from_id": a.id,
                "to_id": b.id,
                "length_nmi": round(length, 2),
                "closest_nm": round(dist, 2),
                "band": band,
                "color": band_color(band),
                "impacted": dist <= BAND_JAM_NM,
            }
        )

    return {
        "segments": segments,
        "closest_index": closest_index,
        "closest_nm": round(closest_nm, 2) if closest_nm < float("inf") else None,
        "cumulative_nmi": [round(x, 2) for x in cumulative],
        "band": band_for_distance(closest_nm) if closest_nm < float("inf") else "OUT",
    }


def assess_route_threats(route: Route, threats: list[Threat]) -> list[dict[str, Any]]:
    rows = []
    for threat in threats:
        if len(route.waypoints) < 2:
            # Degenerate home-only route — use home distance
            dist = haversine_nmi(route.waypoints[0].location, threat.location)
            impact = {
                "segments": [],
                "closest_index": 0,
                "closest_nm": round(dist, 2),
                "cumulative_nmi": [0.0],
                "band": band_for_distance(dist),
            }
        else:
            impact = build_impact_segments(route.waypoints, threat)
        if impact["closest_nm"] is None or impact["closest_nm"] > BAND_JAM_NM:
            continue
        rows.append(
            {
                "threat_id": threat.id,
                "threat_kind": threat.kind,
                "threat_label": threat.label or threat.id,
                "severity": threat.severity,
                "latitude": threat.location.lat,
                "longitude": threat.location.lon,
                "closest_approach_nm": impact["closest_nm"],
                "band": impact["band"],
                "impacted_segment_count": sum(1 for s in impact["segments"] if s["impacted"]),
                "segments": impact["segments"],
                "closest_index": impact["closest_index"],
                "cumulative_nmi": impact["cumulative_nmi"],
            }
        )
    rows.sort(key=lambda r: r["closest_approach_nm"])
    return rows


def build_timeline_events(
    planned: PlannedAircraft,
    tasks_by_id: dict[str, Task],
    *,
    cruise_kt: float = CRUISE_KT,
) -> list[dict[str, Any]]:
    """o-my-debrief-style key events along the route (distance → ETA stub)."""
    route = planned.route
    if route is None:
        return []

    events: list[dict[str, Any]] = []
    t_min = 0.0

    def add(
        event_type: str,
        title: str,
        summary: str,
        marker: str,
        *,
        distance_nmi: float,
        status: str = "planned",
        task_id: Optional[str] = None,
    ) -> None:
        nonlocal t_min
        eta_min = (distance_nmi / cruise_kt) * 60.0 if cruise_kt else 0.0
        events.append(
            {
                "event_id": f"{planned.aircraft_id}-{len(events)+1}",
                "event_type": event_type,
                "title": title,
                "summary": summary,
                "outcome": summary,
                "marker": marker,  # diamond=collect, caret=strike, flag=milestone
                "status": status,
                "distance_nmi": round(distance_nmi, 1),
                "eta_min": round(eta_min, 1),
                "sim_offset": f"+{int(eta_min)}m",
                "task_id": task_id,
            }
        )

    add(
        "LAUNCH",
        f"Launch {planned.label or planned.aircraft_id}",
        f"Depart {planned.home_base_id} (PSAB)",
        "flag",
        distance_nmi=0.0,
        status="planned",
    )

    cum = 0.0
    if route.legs:
        for leg in route.legs:
            cum += leg.distance_nmi
            wp = leg.to_waypoint
            task = tasks_by_id.get(wp.associated_task_id) if wp.associated_task_id else None
            if task and task.type == TaskType.ISR:
                add(
                    "COLLECT",
                    f"Collect {task.id}",
                    task.label or f"ISR at {wp.id}",
                    "diamond",
                    distance_nmi=cum,
                    task_id=task.id,
                )
            elif task and task.type == TaskType.STRIKE:
                add(
                    "STRIKE",
                    f"Strike {task.id}",
                    task.label or f"Strike at {wp.id}",
                    "caret",
                    distance_nmi=cum,
                    task_id=task.id,
                )
            elif wp.kind in ("navaid", "mission"):
                add(
                    "FIX",
                    f"Fix {wp.id}",
                    wp.name or wp.id,
                    "none",
                    distance_nmi=cum,
                )
            elif wp.kind == "airbase" and cum > 0:
                add(
                    "RECOVER",
                    f"Recover {wp.id}",
                    f"Return to {wp.name or wp.id}",
                    "flag",
                    distance_nmi=cum,
                    status="planned",
                )
    else:
        # Home-only: still surface assigned tasks as concurrent events
        for tid in planned.assigned_task_ids:
            task = tasks_by_id.get(tid)
            if not task:
                continue
            marker = "diamond" if task.type == TaskType.ISR else "caret"
            etype = "COLLECT" if task.type == TaskType.ISR else "STRIKE"
            add(
                etype,
                f"{etype.title()} {task.id}",
                task.label or task.id,
                marker,
                distance_nmi=0.0,
                task_id=task.id,
            )

    for tid in planned.unsatisfied_task_ids:
        task = tasks_by_id.get(tid)
        add(
            "SKIP",
            f"Unsatisfied {tid}",
            (task.label if task else tid) + " — no published fix in range",
            "none",
            distance_nmi=route.total_distance_nmi,
            status="skipped",
            task_id=tid,
        )

    if planned.status == "NO-GO":
        add(
            "NOGO",
            "Fuel NO-GO",
            planned.route.infeasible_reason or "Unexecutable due to fuel",
            "none",
            distance_nmi=route.total_distance_nmi,
            status="blocked",
        )
    elif planned.status == "GO" and route.total_distance_nmi > 0:
        # Ensure recover is present
        if not any(e["event_type"] == "RECOVER" for e in events):
            add(
                "RECOVER",
                f"Recover {planned.home_base_id}",
                "Return to PSAB",
                "flag",
                distance_nmi=route.total_distance_nmi,
            )

    return events


def weapons_utilized(aircraft: Aircraft, assigned: list[Task]) -> int:
    strikes = sum(1 for t in assigned if t.type == TaskType.STRIKE)
    if aircraft.weapons_loadout <= 0:
        return 0
    return min(strikes, aircraft.weapons_loadout)


def build_routes_overview(
    plan: PlanCycleResult,
    aircraft: list[Aircraft],
    tasks: list[Task],
    threats: list[Threat],
) -> dict[str, Any]:
    tasks_by_id = {t.id: t for t in tasks}
    ac_by_id = {a.id: a for a in aircraft}

    assigned_tasks: list[Task] = []
    for p in plan.plans:
        for tid in p.assigned_task_ids:
            if tid in tasks_by_id:
                assigned_tasks.append(tasks_by_id[tid])

    isr_n = sum(1 for t in assigned_tasks if t.type == TaskType.ISR)
    strike_n = sum(1 for t in assigned_tasks if t.type == TaskType.STRIKE)
    skipped = list(plan.allocation.unallocated_task_ids)
    # Also count unsatisfied as skipped for metrics
    unsat = []
    for p in plan.plans:
        unsat.extend(p.unsatisfied_task_ids)
    skipped_all = sorted(set(skipped + unsat))

    weapons_total = 0
    weapons_cap = 0
    routes_out: list[dict[str, Any]] = []

    for p in plan.plans:
        if p.status == "idle" or p.route is None:
            continue
        ac = ac_by_id[p.aircraft_id]
        assigned = [tasks_by_id[t] for t in p.assigned_task_ids if t in tasks_by_id]
        wpn = weapons_utilized(ac, assigned)
        weapons_total += wpn
        weapons_cap += ac.weapons_loadout
        threat_rows = assess_route_threats(p.route, threats)
        primary = threat_rows[0] if threat_rows else None
        timeline = build_timeline_events(p, tasks_by_id)

        routes_out.append(
            {
                "aircraft_id": p.aircraft_id,
                "callsign": p.label or p.aircraft_id,
                "aircraft_type": p.aircraft_type,
                "home_base_id": p.home_base_id,
                "status": p.status,
                "route_name": f"{p.label or p.aircraft_id}-RT",
                "assigned_task_ids": list(p.assigned_task_ids),
                "unsatisfied_task_ids": list(p.unsatisfied_task_ids),
                "task_breakout": {
                    "isr": sum(1 for t in assigned if t.type == TaskType.ISR),
                    "strike": sum(1 for t in assigned if t.type == TaskType.STRIKE),
                },
                "weapons_loadout": ac.weapons_loadout,
                "weapons_utilized": wpn,
                "weapons_remaining": max(0, ac.weapons_loadout - wpn),
                "total_distance_nmi": p.route.total_distance_nmi,
                "feasible": p.route.feasible,
                "infeasible_reason": p.route.infeasible_reason,
                "waypoints": [
                    {
                        "id": wp.id,
                        "name": wp.name,
                        "kind": wp.kind,
                        "lat": wp.location.lat,
                        "lon": wp.location.lon,
                        "associated_task_id": wp.associated_task_id,
                    }
                    for wp in p.route.waypoints
                ],
                "legs": [
                    {
                        "from_id": leg.from_waypoint.id,
                        "to_id": leg.to_waypoint.id,
                        "distance_nmi": leg.distance_nmi,
                        "fuel_burn": leg.fuel_burn,
                        "fuel_remaining_after": leg.fuel_remaining_after,
                    }
                    for leg in p.route.legs
                ],
                "fuel": p.fuel.model_dump() if p.fuel else None,
                "threats": threat_rows,
                "primary_threat": primary,
                "timeline_events": timeline,
                "tasks": [
                    {
                        "id": t.id,
                        "type": t.type.value,
                        "label": t.label,
                        "lat": t.location.lat,
                        "lon": t.location.lon,
                        "priority": t.priority,
                    }
                    for t in assigned
                ],
            }
        )

    return {
        "metrics": {
            "aircraft_count": sum(1 for p in plan.plans if p.status != "idle"),
            "aircraft_go": sum(1 for p in plan.plans if p.status == "GO"),
            "aircraft_nogo": sum(1 for p in plan.plans if p.status == "NO-GO"),
            "aircraft_idle": sum(1 for p in plan.plans if p.status == "idle"),
            "assigned_isr": isr_n,
            "assigned_strike": strike_n,
            "assigned_total": isr_n + strike_n,
            "skipped_tasks": len(skipped_all),
            "skipped_task_ids": skipped_all,
            "unallocated_task_ids": list(plan.allocation.unallocated_task_ids),
            "weapons_utilized": weapons_total,
            "weapons_loadout_total": weapons_cap,
        },
        "routes": routes_out,
        "threats": [t.model_dump() for t in threats],
    }
