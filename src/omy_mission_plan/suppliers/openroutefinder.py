"""Optional openRouteFinder adapter — falls back when package unavailable."""

from __future__ import annotations

from .base import SupplierRouteRequest, SupplierRouteResponse
from .fallback import FallbackSupplier


class OpenRouteFinderSupplier:
    """
    Adapter for openRouteFinder (gtxzsxxk / FSUnion).

    Phase 1: if the library is not installed, delegate to FallbackSupplier and
    record a note. Full graph integration is a follow-on ticket.
    """

    source = "openroutefinder"

    def __init__(self, fallback: FallbackSupplier) -> None:
        self._fallback = fallback
        self._orf = None
        try:
            # Optional dependency — not required for the prototype core.
            import openroutefinder  # type: ignore  # noqa: F401

            self._orf = openroutefinder
        except Exception:
            self._orf = None

    def plan(self, request: SupplierRouteRequest) -> SupplierRouteResponse:
        if self._orf is None:
            resp = self._fallback.plan(request)
            return SupplierRouteResponse(
                fixes=resp.fixes,
                total_distance_nmi=resp.total_distance_nmi,
                source=self.source,
                notes=list(resp.notes)
                + [
                    "openRouteFinder not installed — used fallback published-waypoint generator"
                ],
            )
        # Future: call ORF Dijkstra and map fixes. Until then, fallback path.
        resp = self._fallback.plan(request)
        return SupplierRouteResponse(
            fixes=resp.fixes,
            total_distance_nmi=resp.total_distance_nmi,
            source=self.source,
            notes=list(resp.notes)
            + ["openRouteFinder present but adapter uses fallback until spike lands"],
        )
