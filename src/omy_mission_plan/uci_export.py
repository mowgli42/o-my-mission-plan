"""Export a UCI 2.5 MissionPlan bundle from a PlanCycleResult.

JSON routes for o-my-sim stay in export_routes.py (uci.route on launch).
This module adds catalog MissionPlan / RoutePlan / TaskPlan XML for the bus.
"""

from __future__ import annotations

from typing import Any

from .models import Route, Task
from .planning import PlanCycleResult
from .uci_messages import (
    MissionPlan,
    MissionPlanStatus,
    PlannedTask,
    RouteActivity,
    RouteActivityPlan,
    RoutePlan,
    TaskPlan,
    Waypoint,
    build_mission_plan_status_xml,
    build_mission_plan_xml,
    build_route_activity_plan_xml,
    build_route_plan_xml,
    build_task_plan_xml,
)


def _role_for_task(task: Task | None, fallback: str) -> str:
    if task is None:
        return fallback
    return "ISR" if task.type.value == "ISR" else "STRIKE"


def route_to_uci(planned: Any, tasks_by_id: dict[str, Task]) -> RoutePlan | None:
    route: Route | None = planned.route
    if route is None or not route.waypoints:
        return None
    wps = [
        Waypoint(
            latitude=wp.location.lat,
            longitude=wp.location.lon,
            name=wp.name or wp.id,
            eta_minutes=float(i * 8),
        )
        for i, wp in enumerate(route.waypoints)
    ]
    return RoutePlan(
        route_plan_id=f"RP-{planned.aircraft_id}",
        platform_id=planned.aircraft_id,
        route_name=f"{planned.label or planned.aircraft_id}-PKG",
        pattern="transit",
        waypoints=wps,
        description=f"{planned.aircraft_type} GO route" if planned.status == "GO" else planned.status,
    )


def plans_to_uci(
    result: PlanCycleResult,
    tasks: list[Task],
    *,
    mission_plan_id: str = "MSN-GULF-PSAB-01",
    region: str = "gulf",
) -> dict[str, str]:
    tasks_by_id = {t.id: t for t in tasks}
    route_plans: list[RoutePlan] = []
    task_plans: list[TaskPlan] = []
    activity_plans: list[RouteActivityPlan] = []
    threat_ids: list[str] = []

    for planned in result.plans:
        rp = route_to_uci(planned, tasks_by_id)
        if rp:
            route_plans.append(rp)
        planned_tasks: list[PlannedTask] = []
        activities: list[RouteActivity] = []
        for i, tid in enumerate(planned.assigned_task_ids):
            task = tasks_by_id.get(tid)
            loc = task.location if task else None
            pt = PlannedTask(
                task_id=tid,
                role=_role_for_task(task, planned.aircraft_type),
                target_entity_id=tid,
                assigned_platform_id=planned.aircraft_id,
                priority=task.priority if task else 3,
                latitude=loc.lat if loc else 0.0,
                longitude=loc.lon if loc else 0.0,
                target_name=task.label if task else tid,
                start_offset_minutes=20.0 + i * 8.0,
            )
            planned_tasks.append(pt)
            activities.append(
                RouteActivity(
                    activity_id=f"ACT-{tid}",
                    task_id=tid,
                    waypoint_name=tid,
                    offset_minutes=pt.start_offset_minutes,
                )
            )
            threat_ids.append(tid)
        task_plans.append(
            TaskPlan(task_plan_id=f"TP-{planned.aircraft_id}", platform_id=planned.aircraft_id, tasks=planned_tasks)
        )
        if rp:
            activity_plans.append(
                RouteActivityPlan(
                    route_activity_plan_id=f"RAP-{planned.aircraft_id}",
                    route_plan_id=rp.route_plan_id,
                    platform_id=planned.aircraft_id,
                    activities=activities,
                )
            )

    mission = MissionPlan(
        mission_plan_id=mission_plan_id,
        name="PSAB package — fuzzy-reconciler / allocated tasks",
        system_id="PKG-PSAB-01",
        region=region,
        route_plan_ids=[r.route_plan_id for r in route_plans],
        task_plan_ids=[t.task_plan_id for t in task_plans],
        route_activity_plan_ids=[a.route_activity_plan_id for a in activity_plans],
        execution_order=["INGRESS", "ISR", "SEAD", "STRIKE", "EGRESS"],
        threat_entity_ids=threat_ids,
        correlation_id=mission_plan_id,
    )
    status = MissionPlanStatus(
        mission_plan_id=mission_plan_id,
        state="PLANNED",
        detail=f"{result.summary}",
        correlation_id=mission_plan_id,
    )
    xml = {
        "MissionPlan": build_mission_plan_xml(mission),
        "MissionPlanStatus": build_mission_plan_status_xml(status),
        **{r.route_plan_id: build_route_plan_xml(r) for r in route_plans},
        **{t.task_plan_id: build_task_plan_xml(t) for t in task_plans},
        **{a.route_activity_plan_id: build_route_activity_plan_xml(a) for a in activity_plans},
    }
    return xml
