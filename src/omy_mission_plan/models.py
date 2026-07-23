"""Core domain models for o-my mission planning."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    ISR = "ISR"
    STRIKE = "STRIKE"


class AircraftType(str, Enum):
    ISR = "ISR"
    FIGHTER = "FIGHTER"
    BOMBER = "BOMBER"


class LatLon(BaseModel):
    lat: float
    lon: float


class Airbase(BaseModel):
    id: str
    name: str
    location: LatLon


class Navaid(BaseModel):
    id: str
    name: str
    location: LatLon
    navaid_type: str = "VOR"  # VOR, VORTAC, VOR/DME, etc.


class Task(BaseModel):
    id: str
    type: TaskType
    location: LatLon
    priority: int = 0  # higher = more important; stub for future
    label: Optional[str] = None


class Aircraft(BaseModel):
    id: str
    type: AircraftType
    home_base_id: str
    initial_fuel: float = Field(..., description="Fuel units at start")
    burn_rate_per_nmi: float = Field(..., description="Constant fuel units burned per nmi")
    reserve_fuel: float = Field(..., description="Fixed reserve that must remain at end of route")
    label: Optional[str] = None


class Waypoint(BaseModel):
    """A point on a route — airbase, navaid, or task proximity point."""
    id: str
    location: LatLon
    kind: str  # "airbase" | "navaid" | "task_proximity"
    name: Optional[str] = None
    associated_task_id: Optional[str] = None  # set when this waypoint satisfies a task


class Leg(BaseModel):
    from_waypoint: Waypoint
    to_waypoint: Waypoint
    distance_nmi: float
    fuel_burn: float = 0.0  # filled by propagator
    fuel_remaining_after: float = 0.0  # filled by propagator


class Route(BaseModel):
    aircraft_id: str
    waypoints: list[Waypoint]
    legs: list[Leg] = []
    assigned_task_ids: list[str] = []
    total_distance_nmi: float = 0.0
    feasible: Optional[bool] = None  # set by propagator
    infeasible_reason: Optional[str] = None


class FuelState(BaseModel):
    aircraft_id: str
    initial_fuel: float
    reserve_fuel: float
    burn_rate_per_nmi: float
    remaining_after_legs: list[float]  # parallel to route.legs
    final_fuel: float
    feasible: bool
    infeasible_reason: Optional[str] = None


class AllocationResult(BaseModel):
    """Result of one allocation cycle."""
    assignments: dict[str, list[str]]  # aircraft_id -> list of task_ids
    unallocated_task_ids: list[str]
    notes: list[str] = []
