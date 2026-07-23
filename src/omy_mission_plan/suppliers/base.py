"""Pluggable route supplier contracts and registry.

See docs/SUPPLIER-ROUTE-TOOLS.md and docs/INTEGRATION-GUIDE.md.
"""

from __future__ import annotations

import os
from typing import Literal, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from ..models import AircraftType, LatLon


class SupplierFix(BaseModel):
    id: str
    lat: float
    lon: float
    name: Optional[str] = None
    kind: str = "navaid"  # airbase | navaid | mission


class SupplierRouteRequest(BaseModel):
    """Lateral path request to a route supplier."""

    origin_id: str
    origin: LatLon
    destination_id: Optional[str] = None
    destination: Optional[LatLon] = None
    vias: list[str] = Field(default_factory=list)
    avoid_fix_ids: list[str] = Field(default_factory=list)
    approach_axis_label: Optional[str] = None
    aircraft_type_hint: Optional[AircraftType] = None
    # Mission context passed through for fallback generators that associate tasks
    task_ids: list[str] = Field(default_factory=list)
    aircraft_id: Optional[str] = None


class SupplierRouteResponse(BaseModel):
    fixes: list[SupplierFix]
    total_distance_nmi: float = 0.0
    source: str
    notes: list[str] = Field(default_factory=list)


SupplierId = Literal["fallback", "openroutefinder", "costgrid"]


@runtime_checkable
class RouteSupplier(Protocol):
    """Supplier capability: constraints → ordered published fixes."""

    source: str

    def plan(self, request: SupplierRouteRequest) -> SupplierRouteResponse: ...


def configured_supplier_id() -> str:
    return os.environ.get("ROUTE_SUPPLIER", "fallback").strip().lower() or "fallback"
