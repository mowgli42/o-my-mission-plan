"""FastAPI Route Propagation Service + planning API + dark UI."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .models import LatLon, Route, Task, TaskType
from .planning import PlanningSession, make_demo_insert_task
from .propagator import propagate
from . import __version__

STATIC_DIR = Path(__file__).resolve().parent / "static"

session = PlanningSession()

app = FastAPI(
    title="o-my Mission Plan",
    description=(
        "Iterative mission planning: allocate ISR/strike tasks, generate "
        "navaid routes, and propagate fuel feasibility (GO / NO-GO)."
    ),
    version=__version__,
)


class InsertTaskRequest(BaseModel):
    aircraft_id: str = Field(..., examples=["FTR-1"])
    task_id: str = Field(default="STK-NEW", examples=["STK-NEW"])
    type: TaskType = TaskType.STRIKE
    lat: float = Field(default=28.35, examples=[28.35])
    lon: float = Field(default=-80.90, examples=[-80.90])
    priority: int = 3
    label: Optional[str] = "Injected strike (dynamic)"


class PropagateRequest(BaseModel):
    aircraft_id: str
    route: Route


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "o-my-mission-plan", "version": __version__}


@app.get("/api/world")
def get_world():
    return session.snapshot()


@app.post("/api/reset")
def reset_world():
    session.reset()
    return {"status": "reset", "tasks": len(session.tasks), "aircraft": len(session.aircraft)}


@app.post("/api/plan")
def run_plan():
    """Full plan cycle: allocate → route → fuel propagate."""
    return session.run_plan_cycle()


@app.get("/api/plan")
def get_latest_plan():
    if session.latest is None:
        raise HTTPException(status_code=404, detail="No plan yet — POST /api/plan first")
    return session.latest


@app.post("/api/propagate")
def propagate_route(body: PropagateRequest):
    """Propagate fuel for an arbitrary route (Swagger / supplier use)."""
    try:
        from .allocator import aircraft_by_id

        ac = aircraft_by_id(session.aircraft, body.aircraft_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    route, fuel = propagate(body.route.model_copy(deep=True), ac)
    return {"route": route, "fuel": fuel}


@app.post("/api/tasks/insert")
def insert_task(body: InsertTaskRequest):
    """Dynamic task insertion — full re-generate + re-propagate for the aircraft."""
    task = Task(
        id=body.task_id,
        type=body.type,
        location=LatLon(lat=body.lat, lon=body.lon),
        priority=body.priority,
        label=body.label,
    )
    try:
        return session.insert_task(body.aircraft_id, task)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/demo/insert-strike")
def demo_insert_strike(aircraft_id: str = "FTR-1"):
    """Convenience: inject a canned strike task and re-assess the aircraft."""
    # Ensure we have a plan first
    if session.latest is None:
        session.run_plan_cycle()
    task = make_demo_insert_task(task_id=f"STK-DYN-{len(session.tasks) + 1}")
    try:
        return session.insert_task(aircraft_id, task)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Static UI
# ---------------------------------------------------------------------------

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/")
def ui_index():
    index = STATIC_DIR / "index.html"
    if not index.is_file():
        return {
            "message": "UI not built yet — use /docs for Swagger",
            "docs": "/docs",
        }
    return FileResponse(index)
