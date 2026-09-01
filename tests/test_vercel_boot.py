"""Vercel boot behavior — Gulf EOB ingest on startup."""

from __future__ import annotations

from fastapi.testclient import TestClient

from omy_mission_plan.app import app, session


def setup_function():
    session.reset()


def test_gulf_eob_bootstrap_when_enabled(monkeypatch):
    monkeypatch.setenv("INGEST_GULF_EOB", "1")
    with TestClient(app) as client:
        health = client.get("/api/health").json()
        assert health["gulf_eob_bootstrapped"] is True
        assert health["plan_ready"] is True
        assert health["order_of_battle_id"] == "OOB-GULF_THREATS"
        plan = client.get("/api/plan")
        assert plan.status_code == 200
        assert plan.json()["summary"]["aircraft_planned"] >= 1
        uci = client.get("/api/uci/export")
        assert uci.status_code == 200
        assert "OrderOfBattle" in " ".join(uci.json()["xml"].values())
