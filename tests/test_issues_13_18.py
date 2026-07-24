"""Issues #13–#18: archetypes, nav loader, map layers, timeline, platforms."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from omy_mission_plan.app import OPTION_STORE, app, session
from omy_mission_plan.archetypes import VALID_ARCHETYPES
from omy_mission_plan.nav_loader import load_nav_database, parse_earth_nav_dat, xplane_data_path


client = TestClient(app)


def setup_function():
    os.environ.pop("ROUTE_SUPPLIER", None)
    os.environ.pop("NAV_SOURCE", None)
    session.reset()
    OPTION_STORE.clear()


def test_archetype_on_options_and_pool_exceeds_three():
    top = client.post("/api/options/top-three?force=true").json()
    assert top["pool_size"] == 3
    assert top["options"][0]["archetype"] in VALID_ARCHETYPES
    # Contingency beyond pinned trio
    extra = client.post(
        "/api/options",
        json={"label": "Shock contingency", "archetype": "shock"},
    ).json()
    assert extra["archetype"] == "shock"
    assert extra["slot"] is None
    listed = client.get("/api/options").json()
    assert listed["pool_size"] == 4
    assert sum(1 for o in listed["options"] if o["slot"]) == 3

    cmp = client.get("/api/options/compare").json()
    assert "archetypes" in cmp
    assert any(o.get("archetype_fit") for o in cmp["options"])


def test_unpin_keeps_pool_member():
    top = client.post("/api/options/top-three?force=true").json()
    oid = top["slots"]["C"]
    r = client.post(f"/api/options/{oid}/unpin")
    assert r.status_code == 200
    assert r.json()["slot"] is None
    listed = client.get("/api/options").json()
    assert listed["pool_size"] == 3
    assert listed["slots"]["C"] is None


def test_gap_report_stub():
    top = client.post("/api/options/top-three?force=true").json()
    oid = top["slots"]["A"]
    g = client.get(f"/api/options/{oid}/gaps").json()
    assert g["option_id"] == oid
    assert g["archetype"] == "efficient"
    assert g["human_in_the_loop"] is True
    assert "gaps" in g and "risks" in g


def test_xplane_nav_loader_densifies():
    path = xplane_data_path()
    assert path.is_file()
    loaded = parse_earth_nav_dat(path)
    assert len(loaded) >= 10

    os.environ["NAV_SOURCE"] = "xplane"
    session.reset()
    assert session.nav_source == "xplane"
    assert len(session.navaids) > 6  # denser than fixture-only
    world = client.get("/api/world").json()
    assert world["nav_source"] == "xplane"
    assert world["navaid_count"] == len(session.navaids)

    r = client.post("/api/plan")
    assert r.status_code == 200
    for plan in r.json()["plans"]:
        route = plan.get("route")
        if not route:
            continue
        for wp in route["waypoints"]:
            assert not wp["id"].startswith("PROX-")


def test_fixture_nav_fallback():
    os.environ["NAV_SOURCE"] = "fixture"
    nav = load_nav_database()
    assert nav["source"] == "fixture"
    assert nav["navaid_count"] == 6


def test_costgrid_and_exposure_and_timeline_apis():
    client.post("/api/plan")
    cg = client.get("/api/map/costgrid").json()
    assert cg["aggregation"] == "max"
    assert cg["cell_count"] > 0
    assert set(cg["levels"]) >= {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    exp = client.get("/api/map/exposure").json()
    assert exp["sees_mode"] == "jam_or_lethal"
    assert len(exp["platforms"]) >= 1

    tl = client.get("/api/timeline").json()
    assert "tracks" in tl
    assert tl["axis_max_minutes"] >= 0

    pos = client.get("/api/map/positions?t_min=30").json()
    assert pos["t_min"] == 30
    assert len(pos["positions"]) >= 1


def test_platform_order_api():
    order = ["BMB-1", "FTR-1", "ISR-1", "FTR-2", "FTR-3", "ISR-2", "BMB-2"]
    r = client.post(
        "/api/platforms/order",
        json={"order": order, "group_by_type": False},
    )
    assert r.status_code == 200
    assert r.json()["platform_order"][0] == "BMB-1"
    assert r.json()["platform_group_by_type"] is False
    world = client.get("/api/world").json()
    assert world["platform_order"][0] == "BMB-1"


def test_ui_has_new_controls():
    html = client.get("/").text
    assert "tog-costgrid" in html
    assert "Aligned timeline" in html
    assert "Group by type" in html
    assert "Cost grid" in html
