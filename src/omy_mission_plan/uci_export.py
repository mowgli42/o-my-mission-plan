"""Export a UCI 2.5 MissionPlan bundle from a PlanCycleResult.

JSON routes for o-my-sim stay in export_routes.py (uci.route on launch).
This module adds catalog MissionPlan / RoutePlan / TaskPlan XML for the bus.
"""

from __future__ import annotations

from typing import Any

from .models import Route, Task, TaskType
from .planning import PlanCycleResult
from .region_threats import OOB_KIND_BY_CATEGORY
from .uci_messages import (
    DMPI,
    EffectPlan,
    MissionPlan,
    MissionPlanStatus,
    OobRecord,
    OrderOfBattle,
    PlannedTask,
    Prioritization,
    PrioritizationItem,
    RequirementSet,
    RouteActivity,
    RouteActivityPlan,
    RoutePlan,
    TaskPlan,
    Waypoint,
    build_dmpi_xml,
    build_effect_plan_xml,
    build_mission_plan_status_xml,
    build_mission_plan_xml,
    build_order_of_battle_xml,
    build_prioritization_xml,
    build_requirement_set_xml,
    build_route_activity_plan_xml,
    build_route_plan_xml,
    build_task_plan_xml,
)


def _role_for_task(task: Task | None, fallback: str) -> str:
    if task is None:
        return fallback
    if task.target_type == "sam_site":
        return "SEAD"
    return "ISR" if task.type.value == "ISR" else "STRIKE"


def _target_entity_id(task: Task | None, tid: str) -> str:
    if task is not None and task.target_entity_id:
        return task.target_entity_id
    return tid


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
    fixed_threats: list | None = None,
    order_of_battle_id: str = "",
    requirement_set_id: str = "",
) -> dict[str, str]:
    tasks_by_id = {t.id: t for t in tasks}
    route_plans: list[RoutePlan] = []
    task_plans: list[TaskPlan] = []
    activity_plans: list[RouteActivityPlan] = []
    assigned: list[PlannedTask] = []
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
            eid = _target_entity_id(task, tid)
            pt = PlannedTask(
                task_id=tid,
                role=_role_for_task(task, planned.aircraft_type),
                target_entity_id=eid,
                assigned_platform_id=planned.aircraft_id,
                priority=task.priority if task else 3,
                latitude=loc.lat if loc else 0.0,
                longitude=loc.lon if loc else 0.0,
                target_name=task.label if task else tid,
                target_type=task.target_type if task and task.target_type else "",
                start_offset_minutes=20.0 + i * 8.0,
            )
            planned_tasks.append(pt)
            assigned.append(pt)
            activities.append(
                RouteActivity(
                    activity_id=f"ACT-{tid}",
                    task_id=tid,
                    waypoint_name=tid,
                    offset_minutes=pt.start_offset_minutes,
                )
            )
            if eid not in threat_ids:
                threat_ids.append(eid)
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

    if fixed_threats:
        for item in fixed_threats:
            if item.entity_id not in threat_ids:
                threat_ids.append(item.entity_id)

    oob_id = order_of_battle_id or (f"OOB-{region.upper()}" if fixed_threats else "")
    req_id = requirement_set_id or (f"REQ-{oob_id}" if oob_id else "REQ-MSN-GULF-PSAB-01")
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
        order_of_battle_id=oob_id,
        requirement_set_id=req_id,
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

    if fixed_threats:
        records = []
        analyzed: list[str] = []
        for item in fixed_threats:
            attrs = getattr(item, "attributes", {}) or {}
            if getattr(item, "analyzed_at", ""):
                analyzed.append(item.analyzed_at)
            records.append(
                OobRecord(
                    entity_id=item.entity_id,
                    name=item.name,
                    latitude=item.latitude,
                    longitude=item.longitude,
                    category=item.category,
                    kind=OOB_KIND_BY_CATEGORY.get(item.category, "FacilityRecord"),
                    eob_record_id=str(attrs.get("eob_record_id") or item.entity_id),
                    elnot=str(attrs.get("elnot") or ""),
                    be_number=str(attrs.get("be_number") or ""),
                    o_suffix=str(attrs.get("o_suffix") or ""),
                    evaluation_code=str(attrs.get("evaluation_code") or ""),
                    mobility=str(attrs.get("mobility") or "FIXED"),
                    operational_status=str(attrs.get("operational_status") or attrs.get("status") or ""),
                )
            )
        xml["OrderOfBattle"] = build_order_of_battle_xml(
            OrderOfBattle(
                order_of_battle_id=oob_id,
                name=f"{region.upper()}-BASE-EOB",
                valid_from=min(analyzed) if analyzed else "",
                records=records,
                correlation_id=oob_id,
            )
        )

    strike_assigned = [
        pt
        for pt in assigned
        if pt.role in ("STRIKE", "SEAD") or (tasks_by_id.get(pt.task_id) and tasks_by_id[pt.task_id].type is TaskType.STRIKE)
    ]
    dmpis: list[DMPI] = []
    for pt in strike_assigned:
        dmpis.append(
            DMPI(
                dmpi_id=f"DMPI-{pt.target_entity_id}",
                target_entity_id=pt.target_entity_id,
                latitude=pt.latitude,
                longitude=pt.longitude,
                task_id=pt.task_id,
                correlation_id=mission_plan_id,
            )
        )
    dmpi_by_entity = {d.target_entity_id: d.dmpi_id for d in dmpis}
    ranked = sorted(assigned, key=lambda p: (-p.priority, p.task_id))
    pri_items = [
        PrioritizationItem(
            rank=i,
            entity_id=pt.target_entity_id,
            task_id=pt.task_id,
            dmpi_id=dmpi_by_entity.get(pt.target_entity_id, ""),
        )
        for i, pt in enumerate(ranked, start=1)
    ]
    if pri_items:
        xml["Prioritization"] = build_prioritization_xml(
            Prioritization(
                prioritization_id=f"PRI-{mission_plan_id}",
                purpose="F2T2EA_TARGET",
                phase="TARGET",
                mission_plan_id=mission_plan_id,
                items=pri_items,
                correlation_id=mission_plan_id,
            )
        )
    if dmpis:
        xml["DMPI"] = "".join(build_dmpi_xml(d) for d in dmpis)
        xml["EffectPlan"] = build_effect_plan_xml(
            EffectPlan(
                effect_plan_id=f"EFF-{mission_plan_id}",
                mission_plan_id=mission_plan_id,
                task_ids=[pt.task_id for pt in strike_assigned],
                correlation_id=mission_plan_id,
            )
        )
    xml["RequirementSet"] = build_requirement_set_xml(
        RequirementSet(
            requirement_set_id=req_id,
            name="PSAB collection and strike requirements (stub)",
            ready_for_planning=True,
            mission_plan_id=mission_plan_id,
            correlation_id=mission_plan_id,
        )
    )
    return xml
