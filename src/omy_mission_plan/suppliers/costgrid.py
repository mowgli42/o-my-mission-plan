"""Cost-grid supplier — Dijkstra with avoid-zone / avoid-fix penalties."""

from __future__ import annotations

from typing import Optional

from ..models import Threat
from .base import SupplierFix, SupplierRouteRequest, SupplierRouteResponse
from .fallback import FallbackSupplier
from .graph_routing import (
    AvoidZone,
    build_default_graph,
    covering_fix_ids_for_tasks,
    route_via_chain,
)


def zones_from_threats(threats: list[Threat]) -> list[AvoidZone]:
    out: list[AvoidZone] = []
    for t in threats:
        # Soft avoid using jam radius; higher severity → higher penalty
        sev = {"LOW": 1.8, "MEDIUM": 3.0, "HIGH": 5.0, "CRITICAL": 8.0}.get(
            (t.severity or "MEDIUM").upper(), 3.0
        )
        out.append(
            AvoidZone(
                lat=t.location.lat,
                lon=t.location.lon,
                radius_nmi=float(t.jam_radius_nmi or 100.0),
                penalty=sev,
                label=t.id,
            )
        )
    return out


class CostGridSupplier:
    """
    networkx-shaped cost-grid without requiring networkx.

    Edge cost = great-circle distance × avoid-zone penalties; avoided fix ids
    get a large additive penalty so paths prefer other published corridors.
    """

    source = "costgrid"

    def __init__(
        self,
        fallback: FallbackSupplier,
        *,
        threats: Optional[list[Threat]] = None,
        extra_zones: Optional[list[AvoidZone]] = None,
    ) -> None:
        self._fallback = fallback
        self._zones = zones_from_threats(list(threats or []))
        if extra_zones:
            self._zones.extend(extra_zones)
        self._nodes, self._adj = build_default_graph(
            fallback.airbases,
            fallback.navaids,
            fallback.mission_waypoints,
        )

    def plan(self, request: SupplierRouteRequest) -> SupplierRouteResponse:
        origin = request.origin_id
        dest = request.destination_id or request.origin_id
        notes: list[str] = [
            "costgrid: Dijkstra with avoid-zone / avoid-fix penalties on published graph"
        ]
        zones = list(self._zones)
        # Request-level avoid radii around listed fixes (hard preference away)
        for fid in request.avoid_fix_ids or []:
            node = self._nodes.get(fid)
            if node:
                zones.append(
                    AvoidZone(
                        lat=node.location.lat,
                        lon=node.location.lon,
                        radius_nmi=40.0,
                        penalty=6.0,
                        label=f"avoid-{fid}",
                    )
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
                avoid_zones=zones,
                use_penalties=True,
            )
        except KeyError as exc:
            notes.append(f"Cost-grid path failed ({exc}); using fallback")
            resp = self._fallback.plan(request)
            return SupplierRouteResponse(
                fixes=resp.fixes,
                total_distance_nmi=resp.total_distance_nmi,
                source=self.source,
                notes=notes + list(resp.notes),
            )

        # Compare briefly to unpenalized path for notes / demo clarity
        try:
            plain_ids, plain_total = route_via_chain(
                self._nodes,
                self._adj,
                origin,
                dest,
                vias,
                use_penalties=False,
            )
            if path_ids != plain_ids:
                notes.append(
                    f"Avoid penalties changed path vs pure distance "
                    f"({plain_total} nmi → {total} nmi geometric)"
                )
            else:
                notes.append(
                    "Path matches pure-distance route; penalties did not reroute this request"
                )
        except KeyError:
            pass

        if request.avoid_fix_ids:
            notes.append(f"Avoid fix ids: {request.avoid_fix_ids}")
        if zones:
            notes.append(f"Avoid zones applied: {len(zones)}")

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
        return SupplierRouteResponse(
            fixes=fixes,
            total_distance_nmi=total,
            source=self.source,
            notes=notes,
        )
