"""Supplier registry."""

from __future__ import annotations

from typing import Any

from .base import RouteSupplier, configured_supplier_id
from .costgrid import CostGridSupplier
from .fallback import FallbackSupplier
from .openroutefinder import OpenRouteFinderSupplier

__all__ = [
    "RouteSupplier",
    "build_supplier",
    "configured_supplier_id",
    "list_suppliers",
]


def build_supplier(
    supplier_id: str | None = None,
    *,
    airbases: dict,
    navaids: dict,
    mission_waypoints: dict,
    aircraft_by_id: dict,
    tasks_by_id: dict,
) -> RouteSupplier:
    sid = (supplier_id or configured_supplier_id()).lower()
    fallback = FallbackSupplier(
        airbases=airbases,
        navaids=navaids,
        mission_waypoints=mission_waypoints,
        aircraft_by_id=aircraft_by_id,
        tasks_by_id=tasks_by_id,
    )
    if sid in ("fallback", "default"):
        return fallback
    if sid in ("openroutefinder", "orf"):
        return OpenRouteFinderSupplier(fallback)
    if sid in ("costgrid", "grid"):
        return CostGridSupplier(fallback)
    raise ValueError(f"Unknown ROUTE_SUPPLIER: {sid}")


def list_suppliers() -> list[dict[str, Any]]:
    return [
        {
            "id": "fallback",
            "description": "In-repo published-waypoint generator (zero deps)",
            "status": "ready",
        },
        {
            "id": "openroutefinder",
            "description": "Civil Dijkstra adapter (falls back if package missing)",
            "status": "adapter-ready",
        },
        {
            "id": "costgrid",
            "description": "networkx cost-grid / avoid zones (stub → fallback)",
            "status": "stub",
        },
    ]
