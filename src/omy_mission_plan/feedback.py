"""Plan-vs-actual deviation and in-mission retask feedback helpers.

IxDF: visibility of system status + feedback. Color is never the only cue.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from omy_mission_plan.uci_messages import MissionPlanExecutionStatus, RoutePlan, Waypoint

NM_PER_DEG_LAT = 60.0
WATCH_NM = 2.0
OFF_PLAN_NM = 5.0
CRITICAL_NM = 12.0

ATTENTION_KIND_DEVIATION = "PLAN_DEVIATION"
ATTENTION_KIND_RETASK = "RETASK"

# Functional color roles (pair with icon + text — IxDF color in UX)
TONE_BY_SEVERITY = {
    "NONE": "on-plan",
    "WATCH": "watch",
    "OFF_PLAN": "off-plan",
    "CRITICAL": "critical",
}
ICON_BY_SEVERITY = {
    "NONE": "on-plan",
    "WATCH": "watch",
    "OFF_PLAN": "off-plan",
    "CRITICAL": "critical",
}
LABEL_BY_SEVERITY = {
    "NONE": "On plan",
    "WATCH": "Watch — drifting from planned route",
    "OFF_PLAN": "Off plan — platform left the corridor",
    "CRITICAL": "Critical deviation — return-to-plan or replan",
}


@dataclass
class Deviation:
    platform_id: str
    cross_track_nm: float
    along_track_nm: float
    nearest_leg: str
    severity: str

    @property
    def attention_kind(self) -> str:
        return ATTENTION_KIND_DEVIATION if self.severity != "NONE" else ""

    @property
    def tone(self) -> str:
        return TONE_BY_SEVERITY[self.severity]

    @property
    def icon(self) -> str:
        return ICON_BY_SEVERITY[self.severity]

    @property
    def label(self) -> str:
        return LABEL_BY_SEVERITY[self.severity]


def _nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = (lat2 - lat1) * NM_PER_DEG_LAT
    mean_lat = math.radians((lat1 + lat2) / 2)
    dlon = (lon2 - lon1) * NM_PER_DEG_LAT * math.cos(mean_lat)
    return math.hypot(dlat, dlon)


def _point_to_segment_nm(
    lat: float, lon: float, a: Waypoint, b: Waypoint
) -> tuple[float, float]:
    """Return (cross-track nm, along-track nm from a toward b)."""
    ax, ay = 0.0, 0.0
    bx = (b.longitude - a.longitude) * NM_PER_DEG_LAT * math.cos(math.radians(a.latitude))
    by = (b.latitude - a.latitude) * NM_PER_DEG_LAT
    px = (lon - a.longitude) * NM_PER_DEG_LAT * math.cos(math.radians(a.latitude))
    py = (lat - a.latitude) * NM_PER_DEG_LAT
    denom = bx * bx + by * by
    t = 0.0 if denom == 0 else max(0.0, min(1.0, (px * bx + py * by) / denom))
    cx, cy = t * bx, t * by
    cross = math.hypot(px - cx, py - cy)
    along = t * math.hypot(bx, by)
    return cross, along


def measure_deviation(route: RoutePlan, latitude: float, longitude: float) -> Deviation:
    if len(route.waypoints) < 2:
        wp = route.waypoints[0] if route.waypoints else None
        dist = _nm(latitude, longitude, wp.latitude, wp.longitude) if wp else 0.0
        severity = _severity(dist)
        return Deviation(route.platform_id, dist, 0.0, wp.name if wp else "", severity)

    best_cross = 1e9
    best_along = 0.0
    best_leg = ""
    for a, b in zip(route.waypoints, route.waypoints[1:]):
        cross, along = _point_to_segment_nm(latitude, longitude, a, b)
        if cross < best_cross:
            best_cross = cross
            best_along = along
            best_leg = f"{a.name or 'wp'}→{b.name or 'wp'}"
    return Deviation(route.platform_id, best_cross, best_along, best_leg, _severity(best_cross))


def _severity(cross_track_nm: float) -> str:
    if cross_track_nm >= CRITICAL_NM:
        return "CRITICAL"
    if cross_track_nm >= OFF_PLAN_NM:
        return "OFF_PLAN"
    if cross_track_nm >= WATCH_NM:
        return "WATCH"
    return "NONE"


def execution_status(
    *,
    mission_plan_id: str,
    route: RoutePlan,
    latitude: float,
    longitude: float,
    active_task_id: str = "",
    planned_task_id: str = "",
    in_mission_retask: bool = False,
) -> MissionPlanExecutionStatus:
    dev = measure_deviation(route, latitude, longitude)
    if in_mission_retask:
        state = "EXECUTING"
        detail = f"In-mission retask {active_task_id or ''} (planned {planned_task_id or 'none'})"
    elif dev.severity in ("OFF_PLAN", "CRITICAL"):
        state = "OFF_PLAN"
        detail = f"{dev.label} · {dev.cross_track_nm:.1f} nm off {dev.nearest_leg}"
    else:
        state = "ON_PLAN"
        detail = dev.label
    return MissionPlanExecutionStatus(
        mission_plan_id=mission_plan_id,
        platform_id=route.platform_id,
        state=state,
        cross_track_nm=dev.cross_track_nm,
        along_track_nm=dev.along_track_nm,
        deviation_severity=dev.severity,
        active_task_id=active_task_id,
        planned_task_id=planned_task_id,
        in_mission_retask=in_mission_retask,
        detail=detail.strip(),
        correlation_id=mission_plan_id,
    )


def attention_item(status: MissionPlanExecutionStatus) -> dict[str, str | float | int]:
    """Shape consumed by battlespace-manager Attention Rail."""
    if status.in_mission_retask:
        kind = ATTENTION_KIND_RETASK
        title = f"{status.platform_id} retasked in mission"
        tone = "retask"
    elif status.deviation_severity in ("OFF_PLAN", "CRITICAL", "WATCH"):
        kind = ATTENTION_KIND_DEVIATION
        title = f"{status.platform_id} {LABEL_BY_SEVERITY[status.deviation_severity].lower()}"
        tone = TONE_BY_SEVERITY[status.deviation_severity]
    else:
        return {}
    return {
        "kind": kind,
        "title": title,
        "detail": status.detail,
        "tone": tone,
        "icon": ICON_BY_SEVERITY.get(status.deviation_severity, "retask"),
        "entity_id": status.platform_id,
        "priority": 1 if status.deviation_severity == "CRITICAL" or status.in_mission_retask else 2,
    }
