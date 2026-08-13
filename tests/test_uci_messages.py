from __future__ import annotations

from omy_mission_plan.uci_messages import (
    MissionPlan,
    MissionPlanExecutionStatus,
    TaskCommand,
    build_mission_plan_execution_xml,
    build_mission_plan_xml,
    build_task_command_xml,
    parse_mission_plan_execution_xml,
    parse_mission_plan_xml,
    parse_task_command_xml,
)


def test_mission_plan_round_trip():
    plan = MissionPlan(
        mission_plan_id="MSN-TEST-1",
        name="Test package",
        region="gulf",
        route_plan_ids=["RP-A"],
        task_plan_ids=["TP-A"],
        route_activity_plan_ids=["RAP-A"],
        execution_order=["INGRESS", "SEAD", "STRIKE"],
        threat_entity_ids=["GUL-1"],
        correlation_id="MSN-TEST-1",
    )
    xml = build_mission_plan_xml(plan)
    parsed = parse_mission_plan_xml(xml)
    assert parsed.mission_plan_id == "MSN-TEST-1"
    assert parsed.route_plan_ids == ["RP-A"]
    assert parsed.execution_order == ["INGRESS", "SEAD", "STRIKE"]
    assert "MessageType>MissionPlan<" in xml.replace(" ", "") or "MissionPlan" in xml


def test_execution_status_round_trip():
    status = MissionPlanExecutionStatus(
        mission_plan_id="MSN-TEST-1",
        platform_id="COAL-F16C-01",
        state="OFF_PLAN",
        cross_track_nm=6.2,
        deviation_severity="OFF_PLAN",
        active_task_id="TSK-1",
        planned_task_id="TSK-0",
        in_mission_retask=True,
        detail="retask",
        correlation_id="MSN-TEST-1",
    )
    parsed = parse_mission_plan_execution_xml(build_mission_plan_execution_xml(status))
    assert parsed.state == "OFF_PLAN"
    assert parsed.in_mission_retask is True
    assert parsed.cross_track_nm == 6.2


def test_task_command_round_trip():
    cmd = TaskCommand(
        command_id="CMD-1",
        task_id="TSK-NEW",
        platform_id="COAL-FA18-01",
        role="STRIKE",
        target_entity_id="GUL-9",
        mission_plan_id="MSN-TEST-1",
        latitude=29.1,
        longitude=48.0,
        reason="operator pop-up",
        correlation_id="MSN-TEST-1",
    )
    parsed = parse_task_command_xml(build_task_command_xml(cmd))
    assert parsed.role == "STRIKE"
    assert parsed.target_entity_id == "GUL-9"
    assert round(parsed.latitude, 2) == 29.1
