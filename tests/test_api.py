from pathlib import Path

from fastapi.testclient import TestClient

from omy_mission_plan.app import app, session
from omy_mission_plan.export_routes import SCHEMA_ID


client = TestClient(app)


def setup_function():
    session.reset()


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_world_is_gulf_war_psab():
    r = client.get("/api/world")
    data = r.json()
    assert data["scenario_id"] == "gulf-war-psab-001"
    assert data["launch_base_id"] == "OEPS"
    assert len(data["aircraft"]) == 7
    assert all(a["home_base_id"] == "OEPS" for a in data["aircraft"])
    assert len(data["tasks"]) >= 7
    assert len(data["mission_waypoints"]) >= 5
    assert any(b["id"] == "OEPS" for b in data["airbases"])


def test_plan_cycle():
    r = client.post("/api/plan")
    assert r.status_code == 200
    data = r.json()
    assert "allocation" in data
    assert "unallocated_task_ids" in data["allocation"]
    assert "plans" in data
    assert data["summary"]["go"] + data["summary"]["nogo"] + data["summary"]["idle"] == 7
    assert data["summary"]["launch_base_id"] == "OEPS"


def test_dynamic_insert():
    client.post("/api/plan")
    r = client.post(
        "/api/tasks/insert",
        json={
            "aircraft_id": "FTR-1",
            "task_id": "STK-TEST-1",
            "type": "STRIKE",
            "lat": 29.60,
            "lon": 47.65,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "STK-TEST-1" in data["assigned_task_ids"]
    assert data["status"] in ("GO", "NO-GO")
    assert data["route"] is not None
    assert data["fuel"] is not None


def test_ui_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "o-my Mission Plan" in r.text
    assert "PSAB" in r.text


def test_plan_routes_use_published_waypoints_only():
    r = client.post("/api/plan")
    assert r.status_code == 200
    for plan in r.json()["plans"]:
        route = plan.get("route")
        if not route:
            continue
        for wp in route["waypoints"]:
            assert not wp["id"].startswith("PROX-")
            assert wp["kind"] in ("airbase", "navaid", "mission")


def test_export_routes_for_omy_sim(tmp_path: Path):
    client.post("/api/plan")
    r = client.post(
        "/api/routes/export",
        json={"include_nogo": False, "write": True, "directory": str(tmp_path)},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["schema"] == SCHEMA_ID
    assert data["launch_base_id"] == "OEPS"
    assert data["uci"]["route_topic"] == "uci.route"
    assert data["summary"]["route_count"] == len(data["routes"])
    for route in data["routes"]:
        assert route["status"] == "GO"
        assert route["launch"]["when"] == "on_aircraft_launch"
        assert route["launch"]["publish"] is True
        assert route["home_base_id"] == "OEPS"
        assert route["waypoints"][0]["id"] == "OEPS"
        assert route["waypoints"][-1]["id"] == "OEPS"
    latest = tmp_path / "gulf-war-psab-001-routes-latest.json"
    assert latest.is_file()
    assert (tmp_path / "aircraft").is_dir()
