from fastapi.testclient import TestClient

from omy_mission_plan.app import app, session


client = TestClient(app)


def setup_function():
    session.reset()


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_world_inventory():
    r = client.get("/api/world")
    data = r.json()
    assert len(data["aircraft"]) == 7
    assert len(data["tasks"]) >= 7
    assert len(data["navaids"]) >= 5


def test_plan_cycle():
    r = client.post("/api/plan")
    assert r.status_code == 200
    data = r.json()
    assert "allocation" in data
    assert "unallocated_task_ids" in data["allocation"]
    assert "plans" in data
    assert data["summary"]["go"] + data["summary"]["nogo"] + data["summary"]["idle"] == 7


def test_dynamic_insert():
    client.post("/api/plan")
    r = client.post(
        "/api/tasks/insert",
        json={
            "aircraft_id": "FTR-1",
            "task_id": "STK-TEST-1",
            "type": "STRIKE",
            "lat": 28.35,
            "lon": -80.90,
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
