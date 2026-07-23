"""Proximity-based initial route generator using commercial navaids.

The route must bring the aircraft within:
- 80 nmi of each ISR task
- 20 nmi of each strike task

Legs may be any length. Routes start and end at the home airbase.
"""

from __future__ import annotations

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


def proximity_for(task: Task) -> float:
    return ISR_PROXIMITY_NMI if task.type == TaskType.ISR else STRIKE_PROXIMITY_NMI


def _nearest_navaid(location: LatLon, navaids: dict[str, Navaid]) -> Navaid:
    return min(navaids.values(), key=lambda n: haversine_nmi(location, n.location))


def _task_approach_point(task: Task, from_loc: LatLon) -> LatLon:
    """
    Point on the great-circle toward the task that lands just inside the
    required proximity radius (or the task itself if already closer).
    """
    dist = haversine_nmi(from_loc, task.location)
    radius = proximity_for(task)
    if dist <= radius:
        # Already within proximity — use a point slightly offset toward task
        # so the waypoint still "satisfies" the task visually.
        return LatLon(lat=task.location.lat, lon=task.location.lon)

    # Fraction of the way from task back toward from_loc so we stop at radius.
    # We want a point `radius` nmi from the task along the from→task line,
    # i.e. (dist - radius) / dist of the way from from_loc to task.
    frac = (dist - radius * 0.9) / dist
    return LatLon(
        lat=from_loc.lat + frac * (task.location.lat - from_loc.lat),
        lon=from_loc.lon + frac * (task.location.lon - from_loc.lon),
    )


def _nearest_unvisited(current: LatLon, remaining: list[Task]) -> Task:
    return min(remaining, key=lambda t: haversine_nmi(current, t.location))


def generate_route(
    aircraft: Aircraft,
    tasks: list[Task],
    home: Airbase,
    navaids: dict[str, Navaid],
) -> Route:
    """Build home → (navaids / proximity points) → home for assigned tasks."""
    home_wp = Waypoint(
        id=f"HOME-{home.id}",
        location=home.location,
        kind="airbase",
        name=home.name,
    )

    waypoints: list[Waypoint] = [home_wp]
    current = home.location
    remaining = list(tasks)
    assigned_ids = [t.id for t in tasks]

    while remaining:
        task = _nearest_unvisited(current, remaining)
        remaining.remove(task)

        # Insert a helpful navaid if it shortens the path meaningfully
        # and is not already the current point.
        navaid = _nearest_navaid(task.location, navaids)
        navaid_dist = haversine_nmi(current, navaid.location)
        direct = haversine_nmi(current, task.location)
        if (
            navaid_dist > 5.0
            and haversine_nmi(navaid.location, task.location) < direct
            and (not waypoints or waypoints[-1].id != navaid.id)
        ):
            nav_wp = Waypoint(
                id=navaid.id,
                location=navaid.location,
                kind="navaid",
                name=navaid.name,
            )
            waypoints.append(nav_wp)
            current = navaid.location

        approach = _task_approach_point(task, current)
        task_wp = Waypoint(
            id=f"PROX-{task.id}",
            location=approach,
            kind="task_proximity",
            name=task.label or task.id,
            associated_task_id=task.id,
        )
        waypoints.append(task_wp)
        current = approach

    # Return home
    if waypoints[-1].id != home_wp.id:
        waypoints.append(
            Waypoint(
                id=f"HOME-RTN-{home.id}",
                location=home.location,
                kind="airbase",
                name=home.name,
            )
        )

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

    return Route(
        aircraft_id=aircraft.id,
        waypoints=waypoints,
        legs=legs,
        assigned_task_ids=assigned_ids,
        total_distance_nmi=round(total, 2),
    )


def route_satisfies_proximity(route: Route, tasks: list[Task]) -> bool:
    """Verify every task has a waypoint within its proximity radius."""
    by_id = {t.id: t for t in tasks}
    for tid in route.assigned_task_ids:
        task = by_id[tid]
        radius = proximity_for(task)
        ok = any(
            haversine_nmi(wp.location, task.location) <= radius
            for wp in route.waypoints
        )
        if not ok:
            return False
    return True
