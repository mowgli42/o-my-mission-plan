"""FastAPI Route Propagation Service + planning API + dark UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .models import LatLon, Route, Task, TaskType
from .options import (
    OPTION_STORE,
    VALID_EMPHASES,
    compare_options,
    create_option_from_session,
    ensure_top_three,
    rerun_option,
)
from .planning import PlanningSession, make_demo_insert_task
from .propagator import propagate
from .suppliers import list_suppliers
from . import __version__

STATIC_DIR = Path(__file__).resolve().parent / "static"

session = PlanningSession()

app = FastAPI(
    title="o-my Mission Plan",
    description=(
        "Iterative mission planning (Gulf War / PSAB launch): allocate ISR/strike "
        "tasks across Kuwait & Iraq via pluggable route suppliers, propagate fuel "
        "feasibility, keep top-three Mission Options (Efficient / Synchronized / "
        "Unexpected-axis), and export GO routes for o-my-sim launch publish."
    ),
    version=__version__,
)


class InsertTaskRequest(BaseModel):
    aircraft_id: str = Field(..., examples=["FTR-1"])
    task_id: str = Field(default="STK-NEW", examples=["STK-NEW"])
    type: TaskType = TaskType.STRIKE
    lat: float = Field(default=29.60, examples=[29.60])
    lon: float = Field(default=47.65, examples=[47.65])
    priority: int = 3
    label: Optional[str] = "Injected strike (dynamic) — Kuwait north"


class PropagateRequest(BaseModel):
    aircraft_id: str
    route: Route


class ExportRequest(BaseModel):
    include_nogo: bool = False
    write: bool = True
    directory: str = "data/routes"
    option_id: Optional[str] = Field(
        default=None,
        description="Export GO routes from a saved Mission Option (preferred for CONOPS).",
    )


class CreateOptionRequest(BaseModel):
    label: str = "Mission Option"
    emphasis: str = Field(
        default="efficient",
        examples=["efficient", "synchronized", "unexpected_axis"],
    )
    slot: Optional[str] = Field(default=None, examples=["A", "B", "C"])
    supplier_id: Optional[str] = None
    vias: Optional[list[str]] = None
    avoid_fix_ids: Optional[list[str]] = None
    axis_name: Optional[str] = Field(default=None, examples=["northern", "southern", "western"])
    sync_group: str = "wave-1"
    bda_lag_minutes: float = 30.0
    router_input_overrides: Optional[dict[str, Any]] = None


class SlotRequest(BaseModel):
    slot: str = Field(..., examples=["A", "B", "C"])


class RerunOptionRequest(BaseModel):
    router_input_overrides: Optional[dict[str, Any]] = None
    as_new: bool = True
    label: Optional[str] = None


class PreferOptionRequest(BaseModel):
    preferred: bool = True


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "o-my-mission-plan", "version": __version__}


@app.get("/api/world")
def get_world():
    return session.snapshot()


@app.get("/api/suppliers")
def get_suppliers():
    """List pluggable route suppliers (ROUTE_SUPPLIER)."""
    return {
        "active": session.supplier_id,
        "suppliers": list_suppliers(),
        "router_inputs": session.router_inputs,
    }


@app.post("/api/reset")
def reset_world():
    session.reset()
    OPTION_STORE.clear()
    return {
        "status": "reset",
        "tasks": len(session.tasks),
        "aircraft": len(session.aircraft),
        "options_cleared": True,
    }


@app.post("/api/plan")
def run_plan():
    """Full plan cycle: allocate → supplier route → associate tasks → fuel propagate."""
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
    if session.latest is None:
        session.run_plan_cycle()
    task = make_demo_insert_task(task_id=f"STK-DYN-{len(session.tasks) + 1}")
    try:
        return session.insert_task(aircraft_id, task)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/routes/export")
def export_routes(body: Optional[ExportRequest] = None):
    """
    Export final planned routes for o-my-sim.

    Prefer exporting from a chosen Mission Option (`option_id`) after CONOPS
    comparison. Writes `data/routes/<scenario>-routes-latest.json` by default.
    """
    req = body or ExportRequest()
    plan = None
    if req.option_id:
        opt = OPTION_STORE.get(req.option_id)
        if opt is None:
            raise HTTPException(status_code=404, detail=f"Unknown option: {req.option_id}")
        plan = opt.result
    elif session.latest is None:
        raise HTTPException(status_code=404, detail="No plan yet — POST /api/plan first")
    try:
        bundle = session.export_routes_for_sim(
            include_nogo=req.include_nogo,
            directory=req.directory,
            write=req.write,
            plan=plan,
        )
        if req.option_id:
            bundle = {**bundle, "option_id": req.option_id}
        return bundle
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/routes/export")
def get_exported_routes(include_nogo: bool = False, option_id: Optional[str] = None):
    """Return the export bundle without requiring a prior write (does not write)."""
    plan = None
    if option_id:
        opt = OPTION_STORE.get(option_id)
        if opt is None:
            raise HTTPException(status_code=404, detail=f"Unknown option: {option_id}")
        plan = opt.result
    elif session.latest is None:
        raise HTTPException(status_code=404, detail="No plan yet — POST /api/plan first")
    bundle = session.export_routes_for_sim(
        include_nogo=include_nogo, write=False, plan=plan
    )
    if option_id:
        bundle = {**bundle, "option_id": option_id}
    return bundle


@app.get("/api/routes/overview")
def routes_overview():
    """
    Routes screen payload: top metrics, threat impact, debrief-style timelines.

    Aligned with battlespace-manager route display + o-my-debrief key events.
    """
    if session.latest is None:
        raise HTTPException(status_code=404, detail="No plan yet — POST /api/plan first")
    try:
        return session.routes_overview()
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Mission Options (CONOPS top-three)
# ---------------------------------------------------------------------------


@app.post("/api/options")
def create_option(body: CreateOptionRequest):
    """Create a Mission Option: frame emphasis + router inputs → plan cycle."""
    if body.emphasis not in VALID_EMPHASES:
        raise HTTPException(
            status_code=400,
            detail=f"emphasis must be one of {sorted(VALID_EMPHASES)}",
        )
    try:
        opt = create_option_from_session(
            session,
            label=body.label,
            emphasis=body.emphasis,
            slot=body.slot,
            supplier_id=body.supplier_id,
            vias=body.vias,
            avoid_fix_ids=body.avoid_fix_ids,
            axis_name=body.axis_name,
            sync_group=body.sync_group,
            bda_lag_minutes=body.bda_lag_minutes,
            router_input_overrides=body.router_input_overrides,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return opt.to_detail()


@app.post("/api/options/top-three")
def create_top_three(force: bool = False):
    """Ensure slots A/B/C hold Efficient / Synchronized / Unexpected-axis options."""
    created = ensure_top_three(session, force=force)
    return {
        "created": [o.to_list_item() for o in created],
        "slots": OPTION_STORE.slot_map(),
        "options": [o.to_list_item() for o in OPTION_STORE.list_options()],
    }


@app.get("/api/options")
def list_options():
    return {
        "slots": OPTION_STORE.slot_map(),
        "options": [o.to_list_item() for o in OPTION_STORE.list_options()],
    }


@app.get("/api/options/compare")
def options_compare(ids: Optional[str] = Query(default=None, description="Comma-separated option ids")):
    """Side-by-side comparison metrics (human-in-the-loop; no auto picker)."""
    id_list = [x.strip() for x in ids.split(",") if x.strip()] if ids else None
    try:
        return compare_options(id_list)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown option: {exc}") from exc


@app.get("/api/options/{option_id}")
def get_option(option_id: str):
    opt = OPTION_STORE.get(option_id)
    if opt is None:
        raise HTTPException(status_code=404, detail=f"Unknown option: {option_id}")
    return opt.to_detail()


@app.post("/api/options/{option_id}/slot")
def pin_option_slot(option_id: str, body: SlotRequest):
    try:
        opt = OPTION_STORE.assign_slot(option_id, body.slot.upper())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return opt.to_list_item()


@app.post("/api/options/{option_id}/rerun")
def rerun_saved_option(option_id: str, body: Optional[RerunOptionRequest] = None):
    req = body or RerunOptionRequest()
    try:
        opt = rerun_option(
            session,
            option_id,
            router_input_overrides=req.router_input_overrides,
            as_new=req.as_new,
            label=req.label,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return opt.to_detail()


@app.post("/api/options/{option_id}/prefer")
def prefer_option(option_id: str, body: Optional[PreferOptionRequest] = None):
    """Record which option the planner prefers for the next experiment / export."""
    req = body or PreferOptionRequest()
    try:
        if req.preferred:
            opt = OPTION_STORE.set_preferred(option_id)
        else:
            opt = OPTION_STORE.get(option_id)
            if opt is None:
                raise KeyError(option_id)
            opt.preferred = False
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return opt.to_list_item()


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
