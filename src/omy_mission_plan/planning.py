"""Orchestrates one planning cycle and dynamic task insertion."""

from __future__ import annotations

from copy import deepcopy
from typing import Optional

from pydantic import BaseModel, Field

from . import demo_world
from .allocator import allocate, aircraft_by_id
from .models import (
    AllocationResult,
    FuelState,
    LatLon,
    Route,
    Task,
    TaskType,
)
from .propagator import propagate
from .route_generator import generate_route


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
    airbases: list
    navaids: list
    aircraft: list
    tasks: list


class PlanningSession:
    """In-memory session holding the live demo world + latest plans."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.airbases = deepcopy(demo_world.AIRBASES)
        self.navaids = deepcopy(demo_world.NAVAIDS)
        self.aircraft = deepcopy(demo_world.AIRCRAFT)
        self.tasks = deepcopy(demo_world.TASKS)
        self.task_index: dict[str, Task] = {t.id: t for t in self.tasks}
        self.latest: Optional[PlanCycleResult] = None
        # aircraft_id -> assigned task ids (live)
        self.assignments: dict[str, list[str]] = {a.id: [] for a in self.aircraft}
        self.routes: dict[str, Route] = {}
        self.fuel: dict[str, FuelState] = {}

    def snapshot(self) -> WorldSnapshot:
        return WorldSnapshot(
            airbases=list(self.airbases.values()),
            navaids=list(self.navaids.values()),
            aircraft=self.aircraft,
            tasks=self.tasks,
        )

    def run_plan_cycle(self) -> PlanCycleResult:
        allocation = allocate(self.tasks, self.aircraft, self.airbases)
        self.assignments = {aid: list(tids) for aid, tids in allocation.assignments.items()}

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

            home = self.airbases[ac.home_base_id]
            route = generate_route(
                ac, assigned, home, self.navaids, airbases=self.airbases
            )
            route, fuel = propagate(route, ac)
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
            },
        )
        self.latest = result
        return result

    def insert_task(
        self,
        aircraft_id: str,
        task: Task,
    ) -> PlannedAircraft:
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
        home = self.airbases[ac.home_base_id]
        route = generate_route(
            ac, assigned, home, self.navaids, airbases=self.airbases
        )
        route, fuel = propagate(route, ac)
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

        # Refresh latest summary if we have one
        if self.latest:
            updated_plans = []
            for p in self.latest.plans:
                if p.aircraft_id == aircraft_id:
                    updated_plans.append(planned)
                else:
                    updated_plans.append(p)
            self.latest.plans = updated_plans
            self.latest.summary = {
                "aircraft_planned": sum(1 for p in updated_plans if p.status in ("GO", "NO-GO")),
                "go": sum(1 for p in updated_plans if p.status == "GO"),
                "nogo": sum(1 for p in updated_plans if p.status == "NO-GO"),
                "unallocated": len(self.latest.unallocated_tasks),
                "idle": sum(1 for p in updated_plans if p.status == "idle"),
            }

        return planned


def make_demo_insert_task(
    task_id: str = "STK-NEW",
    lat: float = 28.35,
    lon: float = -80.90,
) -> Task:
    return Task(
        id=task_id,
        type=TaskType.STRIKE,
        location=LatLon(lat=lat, lon=lon),
        priority=3,
        label="Injected strike (dynamic)",
    )
