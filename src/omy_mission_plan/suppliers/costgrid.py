"""Cost-grid supplier stub (networkx Dijkstra) — follow-on implementation."""

from __future__ import annotations

from .base import SupplierRouteRequest, SupplierRouteResponse
from .fallback import FallbackSupplier


class CostGridSupplier:
    """
    Placeholder for networkx cost-grid / avoid-zone supplier.

    Registered so ROUTE_SUPPLIER=costgrid is selectable; currently delegates
    to fallback with a clear note. See follow-on ticket for full graph costs.
    """

    source = "costgrid"

    def __init__(self, fallback: FallbackSupplier) -> None:
        self._fallback = fallback

    def plan(self, request: SupplierRouteRequest) -> SupplierRouteResponse:
        resp = self._fallback.plan(request)
        return SupplierRouteResponse(
            fixes=resp.fixes,
            total_distance_nmi=resp.total_distance_nmi,
            source=self.source,
            notes=list(resp.notes)
            + [
                "costgrid supplier stub — avoid penalties not yet applied; using fallback geometry"
            ],
        )
