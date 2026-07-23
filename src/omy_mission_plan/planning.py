"""Orchestrates one planning cycle and dynamic task insertion."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from . import demo_world
from .allocator import allocate, aircraft_by_id
from .export_routes import build_export_bundle, write_export_bundle
from .models import (
    AllocationResult,
    FuelState,
    LatLon,
    Route,
    Task,
    TaskType,
)
from .propagator import propagate
from .route_generator import PublishedFix, generate_route


class PlannedAircraft(BaseModel):
    aircraft_id: str
    label: Optional[str] = None
    aircraft_type: str
    home_base_id: str
    assigned_task_ids: list[str]
    unsatisfied_task_ids: list[str] = Field(default_factory=list)
    route: Optional[Route] = None
    fuel: Optional[FuelState] = None
    status: str  # "idle" | "GO" | "NO-GO"


class PlanCycleResult(BaseModel):
    allocation: AllocationResult
    plans: list[PlannedAircraft]
    unallocated_tasks: list[Task] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)


class WorldSnapshot(BaseModel):
    scenario_id: str
    scenario_name: str
    launch_base_id: str
    airbases: list
    navaids: list
    mission_waypoints: list
    aircraft: list
    tasks: list


class PlanningSession:
    """In-memory session holding the live demo world + latest plans."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.airbases = deepcopy(demo_world.AIRBASES)
        self.navaids = deepcopy(demo_world.NAVAIDS)
        self.mission_waypoints: dict[str, PublishedFix] = dict(
            demo_world.MISSION_WAYPOINTS
        )
        self.aircraft = deepcopy(demo_world.AIRCRAFT)
        self.tasks = deepcopy(demo_world.TASKS)
        self.task_index: dict[str, Task] = {t.id: t for t in self.tasks}
        self.latest: Optional[PlanCycleResult] = None
        self.assignments: dict[str, list[str]] = {a.id: [] for a in self.aircraft}
        self.routes: dict[str, Route] = {}
        self.fuel: dict[str, FuelState] = {}
        self.last_export_paths: dict[str, str] = {}

    def snapshot(self) -> WorldSnapshot:
        return WorldSnapshot(
            scenario_id=demo_world.SCENARIO_ID,
            scenario_name=demo_world.SCENARIO_NAME,
            launch_base_id=demo_world.LAUNCH_BASE_ID,
            airbases=list(self.airbases.values()),
            navaids=list(self.navaids.values()),
            mission_waypoints=[
                {
                    "id": f.id,
                    "name": f.name,
                    "kind": f.kind,
                    "location": {"lat": f.location.lat, "lon": f.location.lon},
                }
                for f in self.mission_waypoints.values()
            ],
            aircraft=self.aircraft,
            tasks=self.tasks,
        )

    def _generate(self, ac, assigned) -> tuple[Route, FuelState]:
        home = self.airbases[ac.home_base_id]
        route = generate_route(
            ac,
            assigned,
            home,
            self.navaids,
            airbases=self.airbases,
            mission_waypoints=self.mission_waypoints,
        )
        return propagate(route, ac)

    def run_plan_cycle(self) -> PlanCycleResult:
        allocation = allocate(self.tasks, self.aircraft, self.airbases)
        self.assignments = {
            aid: list(tids) for aid, tids in allocation.assignments.items()
        }

        plans: list[PlannedAircraft] = []
        self.routes.clear()
        self.fuel.clear()

        for ac in self.aircraft:
            tids = self.assignments.get(ac.id, [])
            assigned = [self.task_index[tid] for tid in tids if tid in self.task_index]
            if not assigned:
                plans.append(
                    PlannedAircraft(
                        aircraft_id=ac.id,
                        label=ac.label,
                        aircraft_type=ac.type.value,
                        home_base_id=ac.home_base_id,
                        assigned_task_ids=[],
                        status="idle",
                    )
                )
                continue

            route, fuel = self._generate(ac, assigned)
            self.routes[ac.id] = route
            self.fuel[ac.id] = fuel
            plans.append(
                PlannedAircraft(
                    aircraft_id=ac.id,
                    label=ac.label,
                    aircraft_type=ac.type.value,
                    home_base_id=ac.home_base_id,
                    assigned_task_ids=tids,
                    unsatisfied_task_ids=list(route.unsatisfied_task_ids),
                    route=route,
                    fuel=fuel,
                    status="GO" if fuel.feasible else "NO-GO",
                )
            )

        unallocated = [self.task_index[tid] for tid in allocation.unallocated_task_ids]
        go = sum(1 for p in plans if p.status == "GO")
        nogo = sum(1 for p in plans if p.status == "NO-GO")
        result = PlanCycleResult(
            allocation=allocation,
            plans=plans,
            unallocated_tasks=unallocated,
            summary={
                "aircraft_planned": go + nogo,
                "go": go,
                "nogo": nogo,
                "unallocated": len(unallocated),
                "idle": sum(1 for p in plans if p.status == "idle"),
                "scenario_id": demo_world.SCENARIO_ID,
                "launch_base_id": demo_world.LAUNCH_BASE_ID,
            },
        )
        self.latest = result
        return result

    def insert_task(self, aircraft_id: str, task: Task) -> PlannedAircraft:
        """Inject a new task, fully re-generate route + re-propagate fuel."""
        if aircraft_id not in {a.id for a in self.aircraft}:
            raise KeyError(f"Unknown aircraft: {aircraft_id}")

        if task.id in self.task_index:
            raise ValueError(f"Task id already exists: {task.id}")

        self.tasks.append(task)
        self.task_index[task.id] = task
        tids = list(self.assignments.get(aircraft_id, []))
        tids.append(task.id)
        self.assignments[aircraft_id] = tids

        ac = aircraft_by_id(self.aircraft, aircraft_id)
        assigned = [self.task_index[tid] for tid in tids]
        route, fuel = self._generate(ac, assigned)
        self.routes[aircraft_id] = route
        self.fuel[aircraft_id] = fuel

        planned = PlannedAircraft(
            aircraft_id=ac.id,
            label=ac.label,
            aircraft_type=ac.type.value,
            home_base_id=ac.home_base_id,
            assigned_task_ids=tids,
            unsatisfied_task_ids=list(route.unsatisfied_task_ids),
            route=route,
            fuel=fuel,
            status="GO" if fuel.feasible else "NO-GO",
        )

        if self.latest:
            updated_plans = [
                planned if p.aircraft_id == aircraft_id else p for p in self.latest.plans
            ]
            self.latest.plans = updated_plans
            self.latest.summary = {
                "aircraft_planned": sum(
                    1 for p in updated_plans if p.status in ("GO", "NO-GO")
                ),
                "go": sum(1 for p in updated_plans if p.status == "GO"),
                "nogo": sum(1 for p in updated_plans if p.status == "NO-GO"),
                "unallocated": len(self.latest.unallocated_tasks),
                "idle": sum(1 for p in updated_plans if p.status == "idle"),
                "scenario_id": demo_world.SCENARIO_ID,
                "launch_base_id": demo_world.LAUNCH_BASE_ID,
            }

        return planned

    def export_routes_for_sim(
        self,
        *,
        include_nogo: bool = False,
        directory: Path | str = "data/routes",
        write: bool = True,
    ) -> dict[str, Any]:
        """Build (and optionally write) the o-my-sim route import bundle."""
        if self.latest is None:
            raise RuntimeError("No plan yet — run a plan cycle first")
        bundle = build_export_bundle(
            self.latest, self.aircraft, include_nogo=include_nogo
        )
        if write:
            self.last_export_paths = write_export_bundle(bundle, directory=directory)
            bundle = {**bundle, "written_paths": dict(self.last_export_paths)}
        return bundle


def make_demo_insert_task(
    task_id: str = "STK-NEW",
    lat: float = 29.60,
    lon: float = 47.65,
) -> Task:
    """Dynamic strike near Mutla Ridge (Kuwait north) published coverage."""
    return Task(
        id=task_id,
        type=TaskType.STRIKE,
        location=LatLon(lat=lat, lon=lon),
        priority=3,
        label="Injected strike (dynamic) — Kuwait north",
    )
