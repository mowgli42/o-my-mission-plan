"""Tests for pluggable suppliers and CONOPS Mission Options."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from omy_mission_plan.app import OPTION_STORE, app, session
from omy_mission_plan.options import (
    DEFAULT_AXIS_PROFILES,
    build_router_inputs,
    compare_options,
    create_option_from_session,
    rerun_option,
)
from omy_mission_plan.route_generator import assert_published_only
from omy_mission_plan.suppliers import build_supplier, list_suppliers


client = TestClient(app)


def setup_function():
    os.environ.pop("ROUTE_SUPPLIER", None)
    session.reset()
    OPTION_STORE.clear()


def test_list_suppliers_includes_fallback():
    ids = {s["id"] for s in list_suppliers()}
    assert {"fallback", "openroutefinder", "costgrid"} <= ids


def test_plan_uses_fallback_supplier_by_default():
    r = client.post("/api/plan")
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["supplier_id"] == "fallback"
    for plan in data["plans"]:
        if plan.get("route"):
            assert plan["supplier_source"] == "fallback"
            for wp in plan["route"]["waypoints"]:
                assert not wp["id"].startswith("PROX-")
                assert wp["kind"] in {"airbase", "navaid", "mission"}


def test_openroutefinder_env_falls_back():
    os.environ["ROUTE_SUPPLIER"] = "openroutefinder"
    session.reset()
    r = client.post("/api/plan")
    assert r.status_code == 200
    sources = {
        p["supplier_source"] for p in r.json()["plans"] if p.get("supplier_source")
    }
    assert sources == {"openroutefinder"}


def test_costgrid_env_selectable():
    os.environ["ROUTE_SUPPLIER"] = "costgrid"
    session.reset()
    r = client.post("/api/plan")
    assert r.status_code == 200
    sources = {
        p["supplier_source"] for p in r.json()["plans"] if p.get("supplier_source")
    }
    assert sources == {"costgrid"}


def test_suppliers_endpoint():
    r = client.get("/api/suppliers")
    assert r.status_code == 200
    assert r.json()["active"] == "fallback"
    assert len(r.json()["suppliers"]) >= 3


def test_create_efficient_option():
    r = client.post(
        "/api/options",
        json={"label": "Eff", "emphasis": "efficient", "slot": "A"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["emphasis"] == "efficient"
    assert data["slot"] == "A"
    assert data["router_inputs"]["vias"] == []
    assert "result" in data
    assert data["go_count"] + data["nogo_count"] + data["idle_count"] == 7


def test_synchronized_stores_timing_metadata():
    r = client.post(
        "/api/options",
        json={
            "label": "Sync",
            "emphasis": "synchronized",
            "slot": "B",
            "sync_group": "wave-alpha",
            "bda_lag_minutes": 45,
        },
    )
    assert r.status_code == 200
    inputs = r.json()["router_inputs"]
    assert inputs["sync_group"] == "wave-alpha"
    assert inputs["bda_lag_minutes"] == 45
    assert inputs["timing_alignment"] == "intent-recorded"


def test_unexpected_axis_includes_vias():
    vias = DEFAULT_AXIS_PROFILES["northern"]
    r = client.post(
        "/api/options",
        json={
            "label": "Axis",
            "emphasis": "unexpected_axis",
            "slot": "C",
            "axis_name": "northern",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["router_inputs"]["vias"] == vias
    # At least one planned aircraft should carry the forced vias in order
    found = False
    for plan in data["result"]["plans"]:
        route = plan.get("route")
        if not route:
            continue
        ids = [wp["id"] for wp in route["waypoints"]]
        # vias appear as a subsequence after home
        pos = 0
        ok = True
        for vid in vias:
            try:
                idx = ids.index(vid, pos)
            except ValueError:
                ok = False
                break
            pos = idx + 1
        if ok:
            found = True
            break
    assert found, "expected forced vias on at least one route"


def test_top_three_and_compare():
    r = client.post("/api/options/top-three")
    assert r.status_code == 200
    slots = r.json()["slots"]
    assert slots["A"] and slots["B"] and slots["C"]

    listed = client.get("/api/options").json()
    emphases = {o["option_id"]: o["emphasis"] for o in listed["options"]}
    assert emphases[slots["A"]] == "efficient"
    assert emphases[slots["B"]] == "synchronized"
    assert emphases[slots["C"]] == "unexpected_axis"

    cmp = client.get("/api/options/compare").json()
    assert cmp["human_in_the_loop"] is True
    assert len(cmp["options"]) == 3
    for row in cmp["options"]:
        assert "go_count" in row
        assert "nogo_count" in row
        assert "unallocated_count" in row
        assert "total_distance_nmi" in row
        assert "emphasis" in row


def test_rerun_creates_child_with_parent_link():
    created = client.post(
        "/api/options",
        json={"label": "Base", "emphasis": "efficient"},
    ).json()
    oid = created["option_id"]
    r = client.post(
        f"/api/options/{oid}/rerun",
        json={
            "as_new": True,
            "router_input_overrides": {
                "emphasis": "unexpected_axis",
                "vias": ["MW-WADI-AL-BATIN", "MW-MUTLA"],
                "axis_name": "western",
            },
            "label": "Patched axis",
        },
    )
    assert r.status_code == 200
    child = r.json()
    assert child["parent_option_id"] == oid
    assert child["emphasis"] == "unexpected_axis"
    assert child["router_inputs"]["vias"] == ["MW-WADI-AL-BATIN", "MW-MUTLA"]


def test_prefer_and_export_from_option():
    top = client.post("/api/options/top-three").json()
    oid = top["slots"]["A"]
    pref = client.post(f"/api/options/{oid}/prefer").json()
    assert pref["preferred"] is True

    exp = client.post(
        "/api/routes/export",
        json={"write": False, "option_id": oid},
    )
    assert exp.status_code == 200
    body = exp.json()
    assert body["option_id"] == oid
    assert body["schema"] == "o-my.mission-plan.routes/v1"
    assert "routes" in body


def test_build_router_inputs_efficient_clears_vias():
    inputs = build_router_inputs("efficient", vias=["MW-MUTLA"])
    # efficient emphasis forces empty vias unless we only pass through build with vias=
    # Our API: efficient always clears vias in build_router_inputs
    assert inputs["vias"] == []


def test_session_helpers_round_trip():
    opt = create_option_from_session(
        session, label="x", emphasis="efficient", slot="A"
    )
    assert opt.slot == "A"
    child = rerun_option(
        session,
        opt.option_id,
        router_input_overrides={"avoid_fix_ids": ["BAH"]},
        as_new=True,
    )
    assert child.parent_option_id == opt.option_id
    assert child.router_inputs["avoid_fix_ids"] == ["BAH"]
    cmp = compare_options([opt.option_id, child.option_id])
    assert len(cmp["options"]) == 2


def test_supplier_build_unknown_raises():
    try:
        build_supplier(
            "nope",
            airbases=session.airbases,
            navaids=session.navaids,
            mission_waypoints=session.mission_waypoints,
            aircraft_by_id={a.id: a for a in session.aircraft},
            tasks_by_id=session.task_index,
        )
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_insert_still_uses_supplier_path():
    client.post("/api/plan")
    r = client.post(
        "/api/tasks/insert",
        json={
            "aircraft_id": "FTR-1",
            "task_id": "STK-SUP-1",
            "type": "STRIKE",
            "lat": 29.60,
            "lon": 47.65,
        },
    )
    assert r.status_code == 200
    assert r.json()["supplier_source"] == "fallback"
    assert_published_only(
        session.routes["FTR-1"]
    )


def test_reset_clears_options():
    client.post("/api/options/top-three")
    assert len(OPTION_STORE.list_options()) == 3
    client.post("/api/reset")
    assert OPTION_STORE.list_options() == []
