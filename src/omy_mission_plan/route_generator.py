"""Initial route generator using published waypoints only.

Routes are sequences of fixes from the navigation database (airbases,
commercial navaids, and optional fixed mission waypoints). Proximity
(80 nmi ISR / 20 nmi strike) is a post-selection success criterion —
the generator never invents lat/lon points at planning time.

See docs/ROUTE-GENERATION.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .geo import haversine_nmi
from .models import (
    Airbase,
    Aircraft,
    LatLon,
    Leg,
    Navaid,
    Route,
    Task,
    TaskType,
    Waypoint,
)

ISR_PROXIMITY_NMI = 80.0
STRIKE_PROXIMITY_NMI = 20.0

# Waypoint kinds allowed in a generated route (published set only).
PUBLISHED_KINDS = frozenset({"airbase", "navaid", "mission"})


@dataclass(frozen=True)
class PublishedFix:
    """A fix from the navigation database (never invented at runtime)."""

    id: str
    name: str
    location: LatLon
    kind: str  # "airbase" | "navaid" | "mission"


def proximity_for(task: Task) -> float:
    return ISR_PROXIMITY_NMI if task.type == TaskType.ISR else STRIKE_PROXIMITY_NMI


def build_published_set(
    airbases: dict[str, Airbase],
    navaids: dict[str, Navaid],
    mission_waypoints: Optional[dict[str, PublishedFix]] = None,
) -> dict[str, PublishedFix]:
    """Merge airbases + navaids + optional fixed mission waypoints."""
    published: dict[str, PublishedFix] = {}
    for base in airbases.values():
        published[base.id] = PublishedFix(
            id=base.id,
            name=base.name,
            location=base.location,
            kind="airbase",
        )
    for nav in navaids.values():
        published[nav.id] = PublishedFix(
            id=nav.id,
            name=nav.name,
            location=nav.location,
            kind="navaid",
        )
    if mission_waypoints:
        for fix in mission_waypoints.values():
            if fix.kind not in PUBLISHED_KINDS:
                raise ValueError(f"Invalid mission waypoint kind: {fix.kind}")
            published[fix.id] = fix
    return published


def _nearest_unvisited(current: LatLon, remaining: list[Task]) -> Task:
    return min(remaining, key=lambda t: haversine_nmi(current, t.location))


def _waypoint_satisfies(wp: Waypoint, task: Task) -> bool:
    return haversine_nmi(wp.location, task.location) <= proximity_for(task)


def _find_satisfying_fix(
    task: Task,
    published: dict[str, PublishedFix],
    current: LatLon,
) -> Optional[PublishedFix]:
    """Nearest published fix (to current position) that lies within the task radius."""
    radius = proximity_for(task)
    candidates = [
        fix
        for fix in published.values()
        if haversine_nmi(fix.location, task.location) <= radius
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda f: haversine_nmi(current, f.location))


def _append_fix(
    waypoints: list[Waypoint],
    fix: PublishedFix,
    task_id: Optional[str] = None,
) -> None:
    """Append a published fix unless it is already the last waypoint."""
    if waypoints and waypoints[-1].id == fix.id:
        if task_id and not waypoints[-1].associated_task_id:
            waypoints[-1].associated_task_id = task_id
        return
    waypoints.append(
        Waypoint(
            id=fix.id,
            location=fix.location,
            kind=fix.kind,
            name=fix.name,
            associated_task_id=task_id,
        )
    )


def _compact(waypoints: list[Waypoint]) -> list[Waypoint]:
    compacted: list[Waypoint] = []
    for wp in waypoints:
        if compacted and compacted[-1].id == wp.id:
            if wp.associated_task_id and not compacted[-1].associated_task_id:
                compacted[-1].associated_task_id = wp.associated_task_id
            continue
        compacted.append(wp)
    return compacted


def _build_legs(waypoints: list[Waypoint]) -> tuple[list[Leg], float]:
    legs: list[Leg] = []
    total = 0.0
    for i in range(len(waypoints) - 1):
        d = haversine_nmi(waypoints[i].location, waypoints[i + 1].location)
        legs.append(
            Leg(
                from_waypoint=waypoints[i],
                to_waypoint=waypoints[i + 1],
                distance_nmi=round(d, 2),
            )
        )
        total += d
    return legs, total


def generate_route(
    aircraft: Aircraft,
    tasks: list[Task],
    home: Airbase,
    navaids: dict[str, Navaid],
    airbases: Optional[dict[str, Airbase]] = None,
    mission_waypoints: Optional[dict[str, PublishedFix]] = None,
    vias: Optional[list[str]] = None,
    avoid_fix_ids: Optional[list[str]] = None,
) -> Route:
    """
    Build home → [forced vias] → published fixes for tasks → home.

    Only airbases, commercial navaids, and fixed mission waypoints appear.
    ``vias`` are required published fix ids inserted in order after home
    (unexpected-axis / corridor support). ``avoid_fix_ids`` are excluded
    from task-satisfaction selection (not from explicit vias).
    """
    bases = airbases if airbases is not None else {home.id: home}
    published = build_published_set(bases, navaids, mission_waypoints)
    published[home.id] = PublishedFix(
        id=home.id,
        name=home.name,
        location=home.location,
        kind="airbase",
    )
    avoided = set(avoid_fix_ids or [])

    waypoints: list[Waypoint] = [
        Waypoint(
            id=home.id,
            location=home.location,
            kind="airbase",
            name=home.name,
        )
    ]
    current = home.location
    assigned_ids = [t.id for t in tasks]
    unsatisfied: list[str] = []
    remaining = list(tasks)

    # Forced published vias (axis / corridor) — must exist in the nav database.
    for via_id in vias or []:
        if via_id not in published:
            raise KeyError(f"Unknown published via fix: {via_id}")
        fix = published[via_id]
        _append_fix(waypoints, fix)
        current = fix.location

    selectable = {
        fid: fix for fid, fix in published.items() if fid not in avoided
    }

    while remaining:
        task = _nearest_unvisited(current, remaining)
        remaining.remove(task)

        covering = next((wp for wp in waypoints if _waypoint_satisfies(wp, task)), None)
        if covering is not None:
            if not covering.associated_task_id:
                covering.associated_task_id = task.id
            continue

        chosen = _find_satisfying_fix(task, selectable, current)
        if chosen is None:
            unsatisfied.append(task.id)
            continue

        _append_fix(waypoints, chosen, task_id=task.id)
        current = chosen.location

    if waypoints[-1].id != home.id:
        waypoints.append(
            Waypoint(
                id=home.id,
                location=home.location,
                kind="airbase",
                name=home.name,
            )
        )

    waypoints = _compact(waypoints)
    legs, total = _build_legs(waypoints)

    return Route(
        aircraft_id=aircraft.id,
        waypoints=waypoints,
        legs=legs,
        assigned_task_ids=assigned_ids,
        unsatisfied_task_ids=unsatisfied,
        total_distance_nmi=round(total, 2),
    )


def associate_tasks(route: Route, tasks: list[Task]) -> Route:
    """
    Bind assigned tasks to existing published waypoints by proximity.

    Does not change geometry — only ``associated_task_id`` and
    ``unsatisfied_task_ids``. Used after a supplier returns ordered fixes.
    """
    by_id = {t.id: t for t in tasks}
    assigned = list(route.assigned_task_ids) or [t.id for t in tasks]
    unsatisfied: list[str] = []
    # Clear prior associations before rebinding
    for wp in route.waypoints:
        wp.associated_task_id = None
    for tid in assigned:
        task = by_id.get(tid)
        if task is None:
            unsatisfied.append(tid)
            continue
        covering = next((wp for wp in route.waypoints if _waypoint_satisfies(wp, task)), None)
        if covering is None:
            unsatisfied.append(tid)
            continue
        if not covering.associated_task_id:
            covering.associated_task_id = tid
    route.assigned_task_ids = assigned
    route.unsatisfied_task_ids = unsatisfied
    return route


def route_satisfies_proximity(route: Route, tasks: list[Task]) -> bool:
    """Verify every assigned task has a published waypoint within radius."""
    by_id = {t.id: t for t in tasks}
    for tid in route.assigned_task_ids:
        task = by_id[tid]
        if not any(_waypoint_satisfies(wp, task) for wp in route.waypoints):
            return False
    return True


def assert_published_only(route: Route) -> None:
    """Raise if any waypoint is not from the published kind set."""
    for wp in route.waypoints:
        if wp.kind not in PUBLISHED_KINDS:
            raise AssertionError(f"Non-published waypoint kind: {wp.kind} id={wp.id}")
        if wp.id.startswith("PROX-") or wp.kind == "task_proximity":
            raise AssertionError(f"Invented proximity waypoint: {wp.id}")
