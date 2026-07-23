"""openRouteFinder-style supplier — Dijkstra on published PSAB nav graph.

Spike notes: the upstream openRouteFinder package is not a hard dependency.
When installed we attempt to use it; otherwise we run an in-process Dijkstra
over the same published fixes (airbases + navaids + mission waypoints), which
is the ORF integration shape documented in docs/ORF-SPIKE.md.
"""

from __future__ import annotations

from typing import Optional

from .base import SupplierFix, SupplierRouteRequest, SupplierRouteResponse
from .fallback import FallbackSupplier
from .graph_routing import (
    build_default_graph,
    covering_fix_ids_for_tasks,
    route_via_chain,
)


class OpenRouteFinderSupplier:
    """
    Civil / ORF-style shortest published-fix path.

    Differs from fallback nearest-task sequencing: builds a nav graph and
    runs Dijkstra origin → [vias] → home, then the core associates tasks.
    """

    source = "openroutefinder"

    def __init__(self, fallback: FallbackSupplier) -> None:
        self._fallback = fallback
        self._orf = None
        try:
            import openroutefinder  # type: ignore  # noqa: F401

            self._orf = openroutefinder
        except Exception:
            self._orf = None

        self._nodes, self._adj = build_default_graph(
            fallback.airbases,
            fallback.navaids,
            fallback.mission_waypoints,
        )

    def plan(self, request: SupplierRouteRequest) -> SupplierRouteResponse:
        origin = request.origin_id
        dest = request.destination_id or request.origin_id
        notes: list[str] = []

        if self._orf is not None:
            notes.append(
                "openRouteFinder package present — spike still uses in-repo "
                "PSAB published-graph Dijkstra (see docs/ORF-SPIKE.md)"
            )
        else:
            notes.append(
                "ORF-style spike: in-repo Dijkstra on PSAB published nav graph "
                "(openRouteFinder package not installed)"
            )

        tasks = [
            self._fallback.tasks_by_id[tid]
            for tid in request.task_ids
            if tid in self._fallback.tasks_by_id
        ]
        cover = covering_fix_ids_for_tasks(self._nodes, tasks, origin_id=origin)
        vias = list(request.vias or []) + [c for c in cover if c not in (request.vias or [])]

        try:
            path_ids, total = route_via_chain(
                self._nodes,
                self._adj,
                origin,
                dest,
                vias,
                avoid_fix_ids=list(request.avoid_fix_ids or []),
                use_penalties=False,
            )
        except KeyError as exc:
            notes.append(f"Graph path failed ({exc}); using fallback generator")
            resp = self._fallback.plan(request)
            return SupplierRouteResponse(
                fixes=resp.fixes,
                total_distance_nmi=resp.total_distance_nmi,
                source=self.source,
                notes=notes + list(resp.notes),
            )

        fixes = [
            SupplierFix(
                id=nid,
                lat=self._nodes[nid].location.lat,
                lon=self._nodes[nid].location.lon,
                name=self._nodes[nid].name,
                kind=self._nodes[nid].kind,
            )
            for nid in path_ids
            if nid in self._nodes
        ]
        if request.vias:
            notes.append(f"Forced vias: {request.vias}")
        if request.approach_axis_label:
            notes.append(f"Axis profile: {request.approach_axis_label}")
        notes.append(f"Graph hops: {max(0, len(path_ids) - 1)}")

        return SupplierRouteResponse(
            fixes=fixes,
            total_distance_nmi=total,
            source=self.source,
            notes=notes,
        )
