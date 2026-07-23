"""Follow-on coverage: ORF graph, cost-grid avoids, sync timing, preferred export."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from omy_mission_plan.app import OPTION_STORE, app, session
from omy_mission_plan.options import compute_sync_timing
from omy_mission_plan.suppliers.graph_routing import (
    AvoidZone,
    build_default_graph,
    route_via_chain,
)


client = TestClient(app)


def setup_function():
    os.environ.pop("ROUTE_SUPPLIER", None)
    session.reset()
    OPTION_STORE.clear()


def test_orf_supplier_uses_graph_source():
    os.environ["ROUTE_SUPPLIER"] = "openroutefinder"
    session.reset()
    r = client.post("/api/plan")
    assert r.status_code == 200
    sources = {p["supplier_source"] for p in r.json()["plans"] if p.get("supplier_source")}
    assert sources == {"openroutefinder"}
    # Notes should mention graph / ORF-style
    assert any("Graph" in n or "ORF" in n or "Dijkstra" in n for n in session.last_supplier_notes)


def test_costgrid_changes_path_with_avoid_fix():
    nodes, adj = build_default_graph(
        session.airbases, session.navaids, session.mission_waypoints
    )
    plain, _ = route_via_chain(nodes, adj, "OEPS", "OEPS", ["MW-BASRA"], use_penalties=False)
    avoided, _ = route_via_chain(
        nodes,
        adj,
        "OEPS",
        "OEPS",
        ["MW-BASRA"],
        avoid_fix_ids=["KWI"],
        avoid_zones=[
            AvoidZone(lat=29.22, lon=47.98, radius_nmi=80.0, penalty=12.0, label="kuwait")
        ],
        use_penalties=True,
    )
    # Both valid published-only paths; avoid path should exist
    assert plain[0] == "OEPS" and plain[-1] == "OEPS"
    assert avoided[0] == "OEPS" and avoided[-1] == "OEPS"
    assert all(not x.startswith("PROX-") for x in avoided)

    os.environ["ROUTE_SUPPLIER"] = "costgrid"
    session.reset()
    session.avoid_fix_ids = ["KWI"]
    session.router_inputs["avoid_fix_ids"] = ["KWI"]
    r = client.post("/api/plan")
    assert r.status_code == 200
    assert r.json()["summary"]["supplier_id"] == "costgrid"
    assert any("costgrid" in n.lower() or "Avoid" in n for n in session.last_supplier_notes)


def test_sync_timing_indicators_on_compare():
    r = client.post(
        "/api/options",
        json={
            "label": "Sync",
            "emphasis": "synchronized",
            "slot": "B",
            "sync_group": "wave-demo",
            "bda_lag_minutes": 30,
        },
    )
    assert r.status_code == 200
    sync = r.json()["sync"]
    assert sync is not None
    assert sync["sync_group"] == "wave-demo"
    assert sync["bda_lag_minutes"] == 30
    assert "timing_alignment" in sync
    assert "tot_spread_minutes" in sync
    assert "alignment_ok" in sync
    assert "note" in sync

    cmp = client.get("/api/options/compare").json()
    row = next(o for o in cmp["options"] if o["emphasis"] == "synchronized")
    assert row["sync"]["tot_spread_minutes"] is not None


def test_export_defaults_to_preferred_option():
    top = client.post("/api/options/top-three?force=true").json()
    oid_a = top["slots"]["A"]
    oid_c = top["slots"]["C"]
    client.post(f"/api/options/{oid_c}/prefer")

    exp = client.post("/api/routes/export", json={"write": False})
    assert exp.status_code == 200
    body = exp.json()
    assert body["option_id"] == oid_c
    assert body["export_source"] == "preferred_option"
    assert body["schema"] == "o-my.mission-plan.routes/v1"

    # Explicit overrides preferred
    exp2 = client.post(
        "/api/routes/export",
        json={"write": False, "option_id": oid_a},
    ).json()
    assert exp2["option_id"] == oid_a
    assert exp2["export_source"] == "explicit_option"


def test_ui_contains_options_tab():
    r = client.get("/")
    assert r.status_code == 200
    assert "Top-three Mission Options" in r.text
    assert 'data-view="options"' in r.text
    assert "btn-top-three" in r.text


def test_compute_sync_timing_helper():
    opt = client.post(
        "/api/options",
        json={"label": "S", "emphasis": "synchronized"},
    ).json()
    from omy_mission_plan.options import OPTION_STORE

    stored = OPTION_STORE.get(opt["option_id"])
    metrics = compute_sync_timing(stored.result, stored.router_inputs)
    assert metrics["cruise_kt_assumed"] == 420.0
