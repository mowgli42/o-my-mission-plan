from __future__ import annotations

from fastapi.testclient import TestClient

from omy_mission_plan.app import app, session
from omy_mission_plan.region_threats import default_fixture_path, load_region_file, threats_from_region

client = TestClient(app)


def setup_function():
    session.reset()


def test_gulf_fixture_is_fixed_threats_only():
    threats = threats_from_region(load_region_file(default_fixture_path()))
    assert threats
    assert all(t.category != "large_airport" for t in threats)
    assert any(t.category == "sam_site" for t in threats)


def test_ingest_region_and_uci_export():
    r = client.post("/api/region/ingest", json={"max_threats": 8, "run_plan": True})
    assert r.status_code == 200
    body = r.json()
    assert body["ingest"]["threats_ingested"] == 8
    assert body["plan"]["summary"]["aircraft_planned"] >= 1
    uci = client.get("/api/uci/export")
    assert uci.status_code == 200
    xml = uci.json()["xml"]
    assert "MissionPlan" in xml
    assert "MessageType>MissionPlan" in xml["MissionPlan"] or "MissionPlan" in xml["MissionPlan"]


def test_deviation_feedback_off_plan():
    client.post("/api/plan")
    planned = session.latest.plans
    flyer = next(p for p in planned if p.route and len(p.route.waypoints) >= 2)
    wp = flyer.route.waypoints[0]
    r = client.post(
        "/api/feedback/deviation",
        json={"aircraft_id": flyer.aircraft_id, "lat": wp.location.lat, "lon": wp.location.lon + 0.25},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"]["deviationSeverity"] in ("WATCH", "OFF_PLAN", "CRITICAL")
    assert data["attention"]["kind"] == "PLAN_DEVIATION"
    assert "icon" in data["attention"] and "title" in data["attention"]


def test_insert_returns_task_command_ack():
    client.post("/api/plan")
    r = client.post(
        "/api/tasks/insert",
        json={
            "aircraft_id": "FTR-1",
            "task_id": "STK-UCI-1",
            "type": "STRIKE",
            "lat": 29.60,
            "lon": 47.65,
        },
    )
    assert r.status_code == 200
    uci = r.json()["uci"]
    assert uci["messageType"] == "TaskCommand"
    assert "TaskCommand" in uci["xml"]
    assert uci["feedback"]["kind"] == "RETASK"


def _blob(xml: dict) -> str:
    return " ".join(xml.values())


def test_eob_identity_keys_pass_through_to_oob():
    fixture = default_fixture_path().parent / "eob_identity.json"
    r = client.post(
        "/api/region/ingest",
        json={"region_file": str(fixture), "max_threats": 10, "run_plan": True},
    )
    assert r.status_code == 200
    uci = client.get("/api/uci/export")
    assert uci.status_code == 200
    xml = uci.json()["xml"]
    oob = xml["OrderOfBattle"]
    assert "MessageType>OrderOfBattle" in oob.replace(" ", "") or "OrderOfBattle" in oob
    assert "EOB-GULF-SAM-001" in oob
    assert "SA6" in oob
    assert "gulf-sam-001" in oob
    assert "gulf-apt-009" not in oob
    task_xml = " ".join(v for k, v in xml.items() if k.startswith("TP-"))
    assert "TargetEntityID" in task_xml
    assert "gulf-sam-001" in task_xml
    assert "EntityID>gulf-sam-001" in xml["MissionPlan"].replace(" ", "") or "gulf-sam-001" in xml["MissionPlan"]


def test_oob_validation_does_not_mutate_routeplan():
    fixture = default_fixture_path().parent / "eob_identity.json"
    client.post("/api/region/ingest", json={"region_file": str(fixture), "run_plan": True})
    before = session.route_waypoint_fingerprint()
    assert before
    r = client.post(
        "/api/uci/validate-oob",
        json={
            "order_of_battle_id": "OOB-EOB-IDENTITY-V2",
            "changed_entity_ids": ["gulf-sam-001"],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["routesUnchanged"] is True
    assert "ORDER_OF_BATTLE" in body["xml"]["MissionPlanValidationCommand"]
    assert body["state"] == "INVALID"
    after = session.route_waypoint_fingerprint()
    assert after == before


def test_strike_export_seeds_dmpi_and_prioritization():
    fixture = default_fixture_path().parent / "eob_identity.json"
    client.post("/api/region/ingest", json={"region_file": str(fixture), "run_plan": True})
    xml = client.get("/api/uci/export").json()["xml"]
    assert "DMPI" in xml
    assert "gulf-bm-003" in xml["DMPI"] or "gulf-sam-001" in xml["DMPI"]
    assert "Prioritization" in xml
    pri = xml["Prioritization"]
    assert "F2T2EA_TARGET" in pri
    assert "gulf-sam-001" in pri or "gulf-bm-003" in pri
    assert "RequirementSet" in xml
    assert "ReadyForPlanning" in xml["RequirementSet"]
