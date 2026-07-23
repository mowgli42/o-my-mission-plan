"""Fallback supplier — in-repo published-waypoint generator (zero deps)."""

from __future__ import annotations

from typing import Optional

from ..geo import haversine_nmi
from ..models import Airbase, Aircraft, Navaid, Task
from ..route_generator import PublishedFix, generate_route
from .base import SupplierFix, SupplierRouteRequest, SupplierRouteResponse


class FallbackSupplier:
    """Wraps generate_route; supports vias / avoids for CONOPS options."""

    source = "fallback"

    def __init__(
        self,
        *,
        airbases: dict[str, Airbase],
        navaids: dict[str, Navaid],
        mission_waypoints: dict[str, PublishedFix],
        aircraft_by_id: dict[str, Aircraft],
        tasks_by_id: dict[str, Task],
    ) -> None:
        self.airbases = airbases
        self.navaids = navaids
        self.mission_waypoints = mission_waypoints
        self.aircraft_by_id = aircraft_by_id
        self.tasks_by_id = tasks_by_id

    def plan(self, request: SupplierRouteRequest) -> SupplierRouteResponse:
        home = self.airbases.get(request.origin_id)
        if home is None:
            raise KeyError(f"Unknown origin airbase: {request.origin_id}")

        ac_id = request.aircraft_id
        if not ac_id or ac_id not in self.aircraft_by_id:
            # Build a lightweight aircraft stub for pure lateral path
            from ..models import AircraftType

            aircraft = Aircraft(
                id=ac_id or "SUPPLIER",
                type=request.aircraft_type_hint or AircraftType.FIGHTER,
                home_base_id=home.id,
                initial_fuel=20000.0,
                burn_rate_per_nmi=10.0,
                reserve_fuel=2000.0,
            )
        else:
            aircraft = self.aircraft_by_id[ac_id]

        tasks = [self.tasks_by_id[tid] for tid in request.task_ids if tid in self.tasks_by_id]
        route = generate_route(
            aircraft,
            tasks,
            home,
            self.navaids,
            airbases=self.airbases,
            mission_waypoints=self.mission_waypoints,
            vias=list(request.vias),
            avoid_fix_ids=list(request.avoid_fix_ids),
        )

        fixes = [
            SupplierFix(
                id=wp.id,
                lat=wp.location.lat,
                lon=wp.location.lon,
                name=wp.name,
                kind=wp.kind,
            )
            for wp in route.waypoints
        ]
        notes = []
        if request.vias:
            notes.append(f"Forced vias: {request.vias}")
        if request.approach_axis_label:
            notes.append(f"Axis profile: {request.approach_axis_label}")
        if route.unsatisfied_task_ids:
            notes.append(f"Unsatisfied tasks: {route.unsatisfied_task_ids}")

        return SupplierRouteResponse(
            fixes=fixes,
            total_distance_nmi=route.total_distance_nmi,
            source=self.source,
            notes=notes,
        )


def response_to_route(
    response: SupplierRouteResponse,
    aircraft_id: str,
    assigned_task_ids: list[str],
    unsatisfied_task_ids: Optional[list[str]] = None,
):
    """Convert supplier fixes into a core Route (legs + distances)."""
    from ..models import LatLon, Leg, Route, Waypoint

    waypoints = [
        Waypoint(
            id=f.id,
            location=LatLon(lat=f.lat, lon=f.lon),
            kind=f.kind if f.kind in {"airbase", "navaid", "mission"} else "navaid",
            name=f.name,
        )
        for f in response.fixes
    ]
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
        aircraft_id=aircraft_id,
        waypoints=waypoints,
        legs=legs,
        assigned_task_ids=list(assigned_task_ids),
        unsatisfied_task_ids=list(unsatisfied_task_ids or []),
        total_distance_nmi=round(total, 2),
    )
