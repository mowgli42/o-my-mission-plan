"""UCI-Lite (Tier B) builders for UCI 2.5 mission-plan catalog elements.

Element names match Open Arsenal UCI 2.5 (``UCI_MessageDefinitions_v2_5_0.xsd``).
Bodies live in program namespace ``urn:omy:mission:1.0`` until Tier C XSD validation.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

NS_UCI = "urn:uci:standard:1.0"
NS_MP = "urn:omy:mission:1.0"
NS_EOB = "urn:omy:eob:1.0"

ET.register_namespace("uci", NS_UCI)
ET.register_namespace("mp", NS_MP)
ET.register_namespace("eob", NS_EOB)

EXECUTION_STATES = ("PLANNED", "ACTIVATING", "EXECUTING", "ON_PLAN", "OFF_PLAN", "COMPLETE", "ABORTED")
TASK_ROLES = ("ISR", "COLLECTION", "STRIKE", "SEAD", "CAS", "CAP", "EW")
DEVIATION_SEVERITIES = ("NONE", "WATCH", "OFF_PLAN", "CRITICAL")


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _q(tag: str, ns: str, text: str | float | int | bool) -> ET.Element:
    el = ET.Element(f"{{{ns}}}{tag}")
    el.text = str(text).lower() if isinstance(text, bool) else str(text)
    return el


def _xml(root: ET.Element) -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def _header(
    msg_type: str,
    sender: str,
    *,
    msg_id: str = "",
    correlation_id: str = "",
) -> ET.Element:
    root = ET.Element(f"{{{NS_UCI}}}Message")
    header = ET.SubElement(root, f"{{{NS_UCI}}}Header")
    header.append(_q("MessageID", NS_UCI, msg_id or f"MP-{uuid4().hex[:12].upper()}"))
    header.append(_q("Timestamp", NS_UCI, _utc_now()))
    header.append(_q("Sender", NS_UCI, sender))
    header.append(_q("MessageType", NS_UCI, msg_type))
    if correlation_id:
        header.append(_q("CorrelationID", NS_UCI, correlation_id))
    return root


def _text(el: ET.Element | None, local: str, ns: str = NS_MP) -> str:
    if el is None:
        return ""
    child = el.find(f"{{{ns}}}{local}")
    return (child.text or "").strip() if child is not None else ""


@dataclass
class Waypoint:
    latitude: float
    longitude: float
    altitude_feet: float = 20000.0
    name: str = ""
    eta_minutes: float = 0.0


@dataclass
class RoutePlan:
    route_plan_id: str
    platform_id: str
    route_name: str
    pattern: str = "transit"
    waypoints: list[Waypoint] = field(default_factory=list)
    speed_kts: float = 420.0
    description: str = ""


@dataclass
class PlannedTask:
    task_id: str
    role: str
    target_entity_id: str
    assigned_platform_id: str
    priority: int = 3
    latitude: float = 0.0
    longitude: float = 0.0
    target_name: str = ""
    target_type: str = ""
    start_offset_minutes: float = 0.0
    predecessor_task_ids: list[str] = field(default_factory=list)
    time_sensitive: bool = False


@dataclass
class TaskPlan:
    task_plan_id: str
    platform_id: str
    tasks: list[PlannedTask] = field(default_factory=list)


@dataclass
class RouteActivity:
    activity_id: str
    task_id: str
    waypoint_name: str
    offset_minutes: float
    action: str = "EXECUTE_TASK"


@dataclass
class RouteActivityPlan:
    route_activity_plan_id: str
    route_plan_id: str
    platform_id: str
    activities: list[RouteActivity] = field(default_factory=list)


@dataclass
class MissionPlan:
    mission_plan_id: str
    name: str
    system_id: str = "PKG-1"
    region: str = ""
    route_plan_ids: list[str] = field(default_factory=list)
    task_plan_ids: list[str] = field(default_factory=list)
    route_activity_plan_ids: list[str] = field(default_factory=list)
    execution_order: list[str] = field(default_factory=list)
    threat_entity_ids: list[str] = field(default_factory=list)
    order_of_battle_id: str = ""
    requirement_set_id: str = ""
    correlation_id: str = ""


@dataclass
class MissionPlanStatus:
    mission_plan_id: str
    state: str
    detail: str = ""
    correlation_id: str = ""


@dataclass
class MissionPlanExecutionStatus:
    """UCI 2.5 MissionPlan execution status plus plan-vs-actual feedback fields."""

    mission_plan_id: str
    platform_id: str
    state: str
    cross_track_nm: float = 0.0
    along_track_nm: float = 0.0
    deviation_severity: str = "NONE"
    active_task_id: str = ""
    planned_task_id: str = ""
    in_mission_retask: bool = False
    detail: str = ""
    correlation_id: str = ""


@dataclass
class TaskCommand:
    """UCI 2.5 TaskCommand — in-mission tasking that must not silently mutate the plan."""

    command_id: str
    task_id: str
    platform_id: str
    role: str
    target_entity_id: str
    mission_plan_id: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    reason: str = ""
    correlation_id: str = ""


def build_route_plan_xml(plan: RoutePlan, sender: str = "o-my-mission-plan") -> str:
    root = _header("RoutePlan", sender, correlation_id=plan.route_plan_id)
    body = ET.SubElement(root, f"{{{NS_MP}}}RoutePlan")
    body.append(_q("RoutePlanID", NS_MP, plan.route_plan_id))
    body.append(_q("PlatformID", NS_MP, plan.platform_id))
    body.append(_q("RouteName", NS_MP, plan.route_name))
    body.append(_q("Pattern", NS_MP, plan.pattern))
    body.append(_q("SpeedKts", NS_MP, plan.speed_kts))
    if plan.description:
        body.append(_q("Description", NS_MP, plan.description))
    wps = ET.SubElement(body, f"{{{NS_MP}}}Waypoints")
    for wp in plan.waypoints:
        node = ET.SubElement(wps, f"{{{NS_MP}}}Waypoint")
        node.append(_q("Latitude", NS_MP, round(wp.latitude, 5)))
        node.append(_q("Longitude", NS_MP, round(wp.longitude, 5)))
        node.append(_q("AltitudeFeet", NS_MP, int(wp.altitude_feet)))
        if wp.name:
            node.append(_q("Name", NS_MP, wp.name))
        if wp.eta_minutes:
            node.append(_q("EtaMinutes", NS_MP, round(wp.eta_minutes, 1)))
    return _xml(root)


def build_task_plan_xml(plan: TaskPlan, sender: str = "o-my-mission-plan") -> str:
    root = _header("TaskPlan", sender, correlation_id=plan.task_plan_id)
    body = ET.SubElement(root, f"{{{NS_MP}}}TaskPlan")
    body.append(_q("TaskPlanID", NS_MP, plan.task_plan_id))
    body.append(_q("PlatformID", NS_MP, plan.platform_id))
    tasks_el = ET.SubElement(body, f"{{{NS_MP}}}Tasks")
    for task in plan.tasks:
        node = ET.SubElement(tasks_el, f"{{{NS_MP}}}Task")
        node.append(_q("TaskID", NS_MP, task.task_id))
        node.append(_q("Role", NS_MP, task.role))
        node.append(_q("TargetEntityID", NS_MP, task.target_entity_id))
        node.append(_q("AssignedPlatformID", NS_MP, task.assigned_platform_id))
        node.append(_q("Priority", NS_MP, task.priority))
        if task.target_name:
            node.append(_q("TargetName", NS_MP, task.target_name))
        if task.target_type:
            node.append(_q("TargetType", NS_MP, task.target_type))
        node.append(_q("StartOffsetMinutes", NS_MP, round(task.start_offset_minutes, 1)))
        if task.time_sensitive:
            node.append(_q("TimeSensitive", NS_MP, True))
        if task.predecessor_task_ids:
            preds = ET.SubElement(node, f"{{{NS_MP}}}Predecessors")
            for pid in task.predecessor_task_ids:
                preds.append(_q("TaskID", NS_MP, pid))
        if task.latitude or task.longitude:
            loc = ET.SubElement(node, f"{{{NS_MP}}}Location")
            loc.append(_q("Latitude", NS_MP, round(task.latitude, 5)))
            loc.append(_q("Longitude", NS_MP, round(task.longitude, 5)))
    return _xml(root)


def build_route_activity_plan_xml(plan: RouteActivityPlan, sender: str = "o-my-mission-plan") -> str:
    root = _header("RouteActivityPlan", sender, correlation_id=plan.route_activity_plan_id)
    body = ET.SubElement(root, f"{{{NS_MP}}}RouteActivityPlan")
    body.append(_q("RouteActivityPlanID", NS_MP, plan.route_activity_plan_id))
    body.append(_q("RoutePlanID", NS_MP, plan.route_plan_id))
    body.append(_q("PlatformID", NS_MP, plan.platform_id))
    acts = ET.SubElement(body, f"{{{NS_MP}}}Activities")
    for act in plan.activities:
        node = ET.SubElement(acts, f"{{{NS_MP}}}Activity")
        node.append(_q("ActivityID", NS_MP, act.activity_id))
        node.append(_q("TaskID", NS_MP, act.task_id))
        node.append(_q("WaypointName", NS_MP, act.waypoint_name))
        node.append(_q("OffsetMinutes", NS_MP, round(act.offset_minutes, 1)))
        node.append(_q("Action", NS_MP, act.action))
    return _xml(root)


def build_mission_plan_xml(plan: MissionPlan, sender: str = "o-my-mission-plan") -> str:
    corr = plan.correlation_id or plan.mission_plan_id
    root = _header("MissionPlan", sender, correlation_id=corr)
    body = ET.SubElement(root, f"{{{NS_MP}}}MissionPlan")
    body.append(_q("MissionPlanID", NS_MP, plan.mission_plan_id))
    body.append(_q("Name", NS_MP, plan.name))
    body.append(_q("SystemID", NS_MP, plan.system_id))
    if plan.region:
        body.append(_q("Region", NS_MP, plan.region))
    subs = ET.SubElement(body, f"{{{NS_MP}}}SubPlans")
    for rid in plan.route_plan_ids:
        subs.append(_q("RoutePlanID", NS_MP, rid))
    for tid in plan.task_plan_ids:
        subs.append(_q("TaskPlanID", NS_MP, tid))
    for aid in plan.route_activity_plan_ids:
        subs.append(_q("RouteActivityPlanID", NS_MP, aid))
    order = ET.SubElement(body, f"{{{NS_MP}}}ExecutionOrder")
    for i, step in enumerate(plan.execution_order, start=1):
        el = _q("Step", NS_MP, step)
        el.set("sequence", str(i))
        order.append(el)
    if plan.threat_entity_ids:
        threats = ET.SubElement(body, f"{{{NS_MP}}}ThreatEntities")
        for eid in plan.threat_entity_ids:
            threats.append(_q("EntityID", NS_MP, eid))
    if plan.order_of_battle_id:
        body.append(_q("OrderOfBattleID", NS_MP, plan.order_of_battle_id))
    if plan.requirement_set_id:
        body.append(_q("RequirementSetID", NS_MP, plan.requirement_set_id))
    return _xml(root)


def build_mission_plan_status_xml(status: MissionPlanStatus, sender: str = "o-my-mission-plan") -> str:
    corr = status.correlation_id or status.mission_plan_id
    root = _header("MissionPlanStatus", sender, correlation_id=corr)
    body = ET.SubElement(root, f"{{{NS_MP}}}MissionPlanStatus")
    body.append(_q("MissionPlanID", NS_MP, status.mission_plan_id))
    body.append(_q("State", NS_MP, status.state))
    if status.detail:
        body.append(_q("Detail", NS_MP, status.detail))
    return _xml(root)


def build_mission_plan_execution_xml(
    status: MissionPlanExecutionStatus, sender: str = "o-my-sim"
) -> str:
    corr = status.correlation_id or status.mission_plan_id
    root = _header("MissionPlanExecutionStatus", sender, correlation_id=corr)
    body = ET.SubElement(root, f"{{{NS_MP}}}MissionPlanExecutionStatus")
    body.append(_q("MissionPlanID", NS_MP, status.mission_plan_id))
    body.append(_q("PlatformID", NS_MP, status.platform_id))
    body.append(_q("State", NS_MP, status.state))
    body.append(_q("CrossTrackNm", NS_MP, round(status.cross_track_nm, 3)))
    body.append(_q("AlongTrackNm", NS_MP, round(status.along_track_nm, 3)))
    body.append(_q("DeviationSeverity", NS_MP, status.deviation_severity))
    if status.active_task_id:
        body.append(_q("ActiveTaskID", NS_MP, status.active_task_id))
    if status.planned_task_id:
        body.append(_q("PlannedTaskID", NS_MP, status.planned_task_id))
    body.append(_q("InMissionRetask", NS_MP, status.in_mission_retask))
    if status.detail:
        body.append(_q("Detail", NS_MP, status.detail))
    return _xml(root)


def build_task_command_xml(cmd: TaskCommand, sender: str = "battlespace-display") -> str:
    corr = cmd.correlation_id or cmd.mission_plan_id or cmd.command_id
    root = _header("TaskCommand", sender, correlation_id=corr)
    body = ET.SubElement(root, f"{{{NS_MP}}}TaskCommand")
    body.append(_q("CommandID", NS_MP, cmd.command_id))
    body.append(_q("TaskID", NS_MP, cmd.task_id))
    body.append(_q("PlatformID", NS_MP, cmd.platform_id))
    body.append(_q("Role", NS_MP, cmd.role))
    body.append(_q("TargetEntityID", NS_MP, cmd.target_entity_id))
    if cmd.mission_plan_id:
        body.append(_q("MissionPlanID", NS_MP, cmd.mission_plan_id))
    if cmd.reason:
        body.append(_q("Reason", NS_MP, cmd.reason))
    if cmd.latitude or cmd.longitude:
        loc = ET.SubElement(body, f"{{{NS_MP}}}Location")
        loc.append(_q("Latitude", NS_MP, round(cmd.latitude, 5)))
        loc.append(_q("Longitude", NS_MP, round(cmd.longitude, 5)))
    return _xml(root)


def parse_mission_plan_xml(xml_body: str) -> MissionPlan:
    root = ET.fromstring(xml_body)
    body = root.find(f"{{{NS_MP}}}MissionPlan")
    if body is None:
        raise ValueError("Not a MissionPlan")
    header = root.find(f"{{{NS_UCI}}}Header")
    corr = ""
    if header is not None:
        corr = header.findtext(f"{{{NS_UCI}}}CorrelationID", "") or ""
    subs = body.find(f"{{{NS_MP}}}SubPlans")
    order_el = body.find(f"{{{NS_MP}}}ExecutionOrder")
    threats_el = body.find(f"{{{NS_MP}}}ThreatEntities")
    return MissionPlan(
        mission_plan_id=_text(body, "MissionPlanID"),
        name=_text(body, "Name"),
        system_id=_text(body, "SystemID") or "PKG-1",
        region=_text(body, "Region"),
        route_plan_ids=[el.text or "" for el in (subs.findall(f"{{{NS_MP}}}RoutePlanID") if subs is not None else [])],
        task_plan_ids=[el.text or "" for el in (subs.findall(f"{{{NS_MP}}}TaskPlanID") if subs is not None else [])],
        route_activity_plan_ids=[
            el.text or "" for el in (subs.findall(f"{{{NS_MP}}}RouteActivityPlanID") if subs is not None else [])
        ],
        execution_order=[el.text or "" for el in (order_el.findall(f"{{{NS_MP}}}Step") if order_el is not None else [])],
        threat_entity_ids=[
            el.text or "" for el in (threats_el.findall(f"{{{NS_MP}}}EntityID") if threats_el is not None else [])
        ],
        order_of_battle_id=_text(body, "OrderOfBattleID"),
        requirement_set_id=_text(body, "RequirementSetID"),
        correlation_id=corr,
    )


def parse_mission_plan_execution_xml(xml_body: str) -> MissionPlanExecutionStatus:
    root = ET.fromstring(xml_body)
    body = root.find(f"{{{NS_MP}}}MissionPlanExecutionStatus")
    if body is None:
        raise ValueError("Not a MissionPlanExecutionStatus")
    header = root.find(f"{{{NS_UCI}}}Header")
    corr = header.findtext(f"{{{NS_UCI}}}CorrelationID", "") if header is not None else ""
    return MissionPlanExecutionStatus(
        mission_plan_id=_text(body, "MissionPlanID"),
        platform_id=_text(body, "PlatformID"),
        state=_text(body, "State"),
        cross_track_nm=float(_text(body, "CrossTrackNm") or 0),
        along_track_nm=float(_text(body, "AlongTrackNm") or 0),
        deviation_severity=_text(body, "DeviationSeverity") or "NONE",
        active_task_id=_text(body, "ActiveTaskID"),
        planned_task_id=_text(body, "PlannedTaskID"),
        in_mission_retask=_text(body, "InMissionRetask").lower() in ("true", "1", "yes"),
        detail=_text(body, "Detail"),
        correlation_id=corr or "",
    )


def parse_task_command_xml(xml_body: str) -> TaskCommand:
    root = ET.fromstring(xml_body)
    body = root.find(f"{{{NS_MP}}}TaskCommand")
    if body is None:
        raise ValueError("Not a TaskCommand")
    header = root.find(f"{{{NS_UCI}}}Header")
    corr = header.findtext(f"{{{NS_UCI}}}CorrelationID", "") if header is not None else ""
    loc = body.find(f"{{{NS_MP}}}Location")
    return TaskCommand(
        command_id=_text(body, "CommandID"),
        task_id=_text(body, "TaskID"),
        platform_id=_text(body, "PlatformID"),
        role=_text(body, "Role"),
        target_entity_id=_text(body, "TargetEntityID"),
        mission_plan_id=_text(body, "MissionPlanID"),
        latitude=float(_text(loc, "Latitude") or 0) if loc is not None else 0.0,
        longitude=float(_text(loc, "Longitude") or 0) if loc is not None else 0.0,
        reason=_text(body, "Reason"),
        correlation_id=corr or "",
    )


@dataclass
class OobRecord:
    entity_id: str
    name: str
    latitude: float
    longitude: float
    category: str
    kind: str
    eob_record_id: str = ""
    elnot: str = ""
    be_number: str = ""
    o_suffix: str = ""
    evaluation_code: str = ""
    mobility: str = "FIXED"
    operational_status: str = ""


@dataclass
class OrderOfBattle:
    order_of_battle_id: str
    name: str
    valid_from: str = ""
    records: list[OobRecord] = field(default_factory=list)
    correlation_id: str = ""


@dataclass
class PrioritizationItem:
    rank: int
    entity_id: str
    task_id: str = ""
    dmpi_id: str = ""


@dataclass
class Prioritization:
    prioritization_id: str
    purpose: str
    phase: str = ""
    mission_plan_id: str = ""
    items: list[PrioritizationItem] = field(default_factory=list)
    correlation_id: str = ""


@dataclass
class DMPI:
    dmpi_id: str
    target_entity_id: str
    latitude: float
    longitude: float
    elevation_feet: float = 0.0
    task_id: str = ""
    weapon_effect: str = ""
    correlation_id: str = ""


@dataclass
class RequirementSet:
    requirement_set_id: str
    name: str
    ready_for_planning: bool = True
    mission_plan_id: str = ""
    correlation_id: str = ""


@dataclass
class EffectPlan:
    effect_plan_id: str
    mission_plan_id: str
    task_ids: list[str] = field(default_factory=list)
    correlation_id: str = ""


@dataclass
class MissionPlanValidationCommand:
    mission_plan_id: str
    reason: str
    order_of_battle_id: str
    changed_entity_ids: list[str] = field(default_factory=list)
    correlation_id: str = ""


def build_order_of_battle_xml(oob: OrderOfBattle, sender: str = "o-my-mission-plan") -> str:
    corr = oob.correlation_id or oob.order_of_battle_id
    root = _header("OrderOfBattle", sender, correlation_id=corr)
    body = ET.SubElement(root, f"{{{NS_EOB}}}OrderOfBattle")
    body.append(_q("OrderOfBattleID", NS_EOB, oob.order_of_battle_id))
    body.append(_q("Name", NS_EOB, oob.name))
    if oob.valid_from:
        body.append(_q("ValidFrom", NS_EOB, oob.valid_from))
    recs = ET.SubElement(body, f"{{{NS_EOB}}}Records")
    for rec in oob.records:
        node = ET.SubElement(recs, f"{{{NS_EOB}}}Record")
        node.append(_q("EOB_RecordID", NS_EOB, rec.eob_record_id or rec.entity_id))
        node.append(_q("EntityID", NS_EOB, rec.entity_id))
        node.append(_q("Name", NS_EOB, rec.name))
        node.append(_q("Category", NS_EOB, rec.category))
        node.append(_q("Kind", NS_EOB, rec.kind))
        pos = ET.SubElement(node, f"{{{NS_EOB}}}Position")
        pos.append(_q("Latitude", NS_EOB, round(rec.latitude, 6)))
        pos.append(_q("Longitude", NS_EOB, round(rec.longitude, 6)))
        if rec.elnot:
            node.append(_q("ELNOT", NS_EOB, rec.elnot))
        if rec.be_number:
            node.append(_q("BE_Number", NS_EOB, rec.be_number))
        if rec.o_suffix:
            node.append(_q("O_Suffix", NS_EOB, rec.o_suffix))
        if rec.evaluation_code:
            node.append(_q("EvaluationCode", NS_EOB, rec.evaluation_code))
        node.append(_q("Mobility", NS_EOB, rec.mobility or "FIXED"))
        if rec.operational_status:
            node.append(_q("OperationalStatus", NS_EOB, rec.operational_status))
    return _xml(root)


def build_prioritization_xml(pri: Prioritization, sender: str = "o-my-mission-plan") -> str:
    corr = pri.correlation_id or pri.mission_plan_id or pri.prioritization_id
    root = _header("Prioritization", sender, correlation_id=corr)
    body = ET.SubElement(root, f"{{{NS_MP}}}Prioritization")
    body.append(_q("PrioritizationID", NS_MP, pri.prioritization_id))
    body.append(_q("Purpose", NS_MP, pri.purpose))
    if pri.phase:
        body.append(_q("Phase", NS_MP, pri.phase))
    if pri.mission_plan_id:
        body.append(_q("MissionPlanID", NS_MP, pri.mission_plan_id))
    items = ET.SubElement(body, f"{{{NS_MP}}}Items")
    for item in pri.items:
        node = ET.SubElement(items, f"{{{NS_MP}}}Item")
        node.append(_q("Rank", NS_MP, item.rank))
        node.append(_q("EntityID", NS_MP, item.entity_id))
        if item.task_id:
            node.append(_q("TaskID", NS_MP, item.task_id))
        if item.dmpi_id:
            node.append(_q("DMPI_ID", NS_MP, item.dmpi_id))
    return _xml(root)


def build_dmpi_xml(dmpi: DMPI, sender: str = "o-my-mission-plan") -> str:
    corr = dmpi.correlation_id or dmpi.target_entity_id
    root = _header("DMPI", sender, correlation_id=corr)
    body = ET.SubElement(root, f"{{{NS_MP}}}DMPI")
    body.append(_q("DMPI_ID", NS_MP, dmpi.dmpi_id))
    body.append(_q("TargetEntityID", NS_MP, dmpi.target_entity_id))
    body.append(_q("Latitude", NS_MP, round(dmpi.latitude, 5)))
    body.append(_q("Longitude", NS_MP, round(dmpi.longitude, 5)))
    body.append(_q("ElevationFeet", NS_MP, int(dmpi.elevation_feet)))
    if dmpi.task_id:
        body.append(_q("TaskID", NS_MP, dmpi.task_id))
    if dmpi.weapon_effect:
        body.append(_q("WeaponEffect", NS_MP, dmpi.weapon_effect))
    return _xml(root)


def build_requirement_set_xml(req: RequirementSet, sender: str = "o-my-mission-plan") -> str:
    corr = req.correlation_id or req.mission_plan_id or req.requirement_set_id
    root = _header("RequirementSet", sender, correlation_id=corr)
    body = ET.SubElement(root, f"{{{NS_MP}}}RequirementSet")
    body.append(_q("RequirementSetID", NS_MP, req.requirement_set_id))
    body.append(_q("Name", NS_MP, req.name))
    body.append(_q("ReadyForPlanning", NS_MP, req.ready_for_planning))
    if req.mission_plan_id:
        body.append(_q("MissionPlanID", NS_MP, req.mission_plan_id))
    return _xml(root)


def build_effect_plan_xml(plan: EffectPlan, sender: str = "o-my-mission-plan") -> str:
    corr = plan.correlation_id or plan.mission_plan_id
    root = _header("EffectPlan", sender, correlation_id=corr)
    body = ET.SubElement(root, f"{{{NS_MP}}}EffectPlan")
    body.append(_q("EffectPlanID", NS_MP, plan.effect_plan_id))
    body.append(_q("MissionPlanID", NS_MP, plan.mission_plan_id))
    tasks = ET.SubElement(body, f"{{{NS_MP}}}Tasks")
    for tid in plan.task_ids:
        tasks.append(_q("TaskID", NS_MP, tid))
    return _xml(root)


def build_mission_plan_validation_xml(
    cmd: MissionPlanValidationCommand, sender: str = "o-my-mission-plan"
) -> str:
    corr = cmd.correlation_id or cmd.mission_plan_id
    root = _header("MissionPlanValidationCommand", sender, correlation_id=corr)
    body = ET.SubElement(root, f"{{{NS_MP}}}MissionPlanValidationCommand")
    body.append(_q("MissionPlanID", NS_MP, cmd.mission_plan_id))
    body.append(_q("Reason", NS_MP, cmd.reason))
    body.append(_q("OrderOfBattleID", NS_MP, cmd.order_of_battle_id))
    changed = ET.SubElement(body, f"{{{NS_MP}}}ChangedEntities")
    for eid in cmd.changed_entity_ids:
        changed.append(_q("EntityID", NS_MP, eid))
    return _xml(root)


def parse_mission_plan_validation_xml(xml_body: str) -> MissionPlanValidationCommand:
    root = ET.fromstring(xml_body)
    body = root.find(f"{{{NS_MP}}}MissionPlanValidationCommand")
    if body is None:
        raise ValueError("Not a MissionPlanValidationCommand")
    header = root.find(f"{{{NS_UCI}}}Header")
    corr = header.findtext(f"{{{NS_UCI}}}CorrelationID", "") if header is not None else ""
    changed_el = body.find(f"{{{NS_MP}}}ChangedEntities")
    return MissionPlanValidationCommand(
        mission_plan_id=_text(body, "MissionPlanID"),
        reason=_text(body, "Reason"),
        order_of_battle_id=_text(body, "OrderOfBattleID"),
        changed_entity_ids=[
            el.text or "" for el in (changed_el.findall(f"{{{NS_MP}}}EntityID") if changed_el is not None else [])
        ],
        correlation_id=corr or "",
    )
