from __future__ import annotations

from omy_mission_plan.feedback import (
    ATTENTION_KIND_DEVIATION,
    ATTENTION_KIND_RETASK,
    attention_item,
    execution_status,
    measure_deviation,
)
from omy_mission_plan.uci_messages import RoutePlan, Waypoint


def _route() -> RoutePlan:
    return RoutePlan(
        route_plan_id="RP-1",
        platform_id="COAL-F16C-01",
        route_name="VIPER01-PKG",
        waypoints=[
            Waypoint(28.0, 48.0, name="INGRESS"),
            Waypoint(29.0, 48.0, name="IP"),
            Waypoint(30.0, 48.0, name="TGT"),
        ],
    )


def test_on_plan_when_on_track():
    dev = measure_deviation(_route(), 29.0, 48.0)
    assert dev.severity == "NONE"
    assert dev.cross_track_nm < 1.0


def test_off_plan_when_east_of_corridor():
    # ~8 nm east of the 48E meridian at 29N
    dev = measure_deviation(_route(), 29.0, 48.15)
    assert dev.severity in ("OFF_PLAN", "CRITICAL", "WATCH")
    assert dev.cross_track_nm > 2.0


def test_execution_status_and_attention_for_deviation():
    status = execution_status(
        mission_plan_id="MSN-1",
        route=_route(),
        latitude=29.0,
        longitude=48.2,
    )
    assert status.state == "OFF_PLAN"
    item = attention_item(status)
    assert item["kind"] == ATTENTION_KIND_DEVIATION
    assert item["tone"] != item["kind"]  # color/tone is not the only cue
    assert "icon" in item and "title" in item


def test_retask_attention_even_if_on_plan():
    status = execution_status(
        mission_plan_id="MSN-1",
        route=_route(),
        latitude=29.0,
        longitude=48.0,
        active_task_id="TSK-POPUP",
        planned_task_id="TSK-SEAD",
        in_mission_retask=True,
    )
    item = attention_item(status)
    assert item["kind"] == ATTENTION_KIND_RETASK
    assert status.in_mission_retask is True
