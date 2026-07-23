"""Published-fix graph routing (Dijkstra) for supplier adapters.

Used by the openRouteFinder-style spike and the cost-grid avoid-zone supplier.
Zero hard dependencies — pure Python heapq Dijkstra over published fixes only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Iterable, Optional

from ..geo import haversine_nmi
from ..models import Airbase, LatLon, Navaid
from ..route_generator import PublishedFix, build_published_set


@dataclass(frozen=True)
class AvoidZone:
    lat: float
    lon: float
    radius_nmi: float
    penalty: float = 5.0  # multiplicative cost factor inside zone
    label: Optional[str] = None


@dataclass
class GraphNode:
    id: str
    location: LatLon
    name: Optional[str]
    kind: str


def _loc(lat: float, lon: float) -> LatLon:
    return LatLon(lat=lat, lon=lon)


def build_nodes(
    airbases: dict[str, Airbase],
    navaids: dict[str, Navaid],
    mission_waypoints: Optional[dict[str, PublishedFix]] = None,
) -> dict[str, GraphNode]:
    published = build_published_set(airbases, navaids, mission_waypoints)
    return {
        fid: GraphNode(id=f.id, location=f.location, name=f.name, kind=f.kind)
        for fid, f in published.items()
    }


def _k_nearest_edges(
    nodes: dict[str, GraphNode],
    *,
    k: int = 6,
    max_link_nmi: float = 450.0,
) -> dict[str, list[tuple[str, float]]]:
    """Connect each fix to its k nearest neighbors within max_link_nmi."""
    ids = list(nodes.keys())
    adj: dict[str, list[tuple[str, float]]] = {i: [] for i in ids}
    for i, a in enumerate(ids):
        dists: list[tuple[float, str]] = []
        for b in ids:
            if a == b:
                continue
            d = haversine_nmi(nodes[a].location, nodes[b].location)
            if d <= max_link_nmi:
                dists.append((d, b))
        dists.sort()
        for d, b in dists[:k]:
            adj[a].append((b, d))
            # undirected
            if (a, d) not in [(x, y) for x, y in adj[b] if x == a]:
                adj[b].append((a, d))
    return adj


def edge_cost(
    dist_nmi: float,
    a: GraphNode,
    b: GraphNode,
    *,
    avoid_fix_ids: set[str],
    avoid_zones: list[AvoidZone],
    avoid_node_penalty: float = 25.0,
) -> float:
    """Distance plus avoid penalties (cost-grid)."""
    cost = dist_nmi
    if a.id in avoid_fix_ids or b.id in avoid_fix_ids:
        cost += avoid_node_penalty * 10.0
    # Midpoint soft avoid
    mid = _loc((a.location.lat + b.location.lat) / 2.0, (a.location.lon + b.location.lon) / 2.0)
    for zone in avoid_zones:
        zloc = _loc(zone.lat, zone.lon)
        if haversine_nmi(mid, zloc) <= zone.radius_nmi:
            cost *= max(1.0, zone.penalty)
        elif haversine_nmi(a.location, zloc) <= zone.radius_nmi:
            cost *= max(1.0, zone.penalty * 0.85)
        elif haversine_nmi(b.location, zloc) <= zone.radius_nmi:
            cost *= max(1.0, zone.penalty * 0.85)
    return cost


def dijkstra(
    adj: dict[str, list[tuple[str, float]]],
    nodes: dict[str, GraphNode],
    origin_id: str,
    dest_id: str,
    *,
    avoid_fix_ids: Optional[Iterable[str]] = None,
    avoid_zones: Optional[list[AvoidZone]] = None,
    use_penalties: bool = False,
) -> tuple[list[str], float]:
    """Return (path_ids, total_distance_nmi). Raises KeyError if unreachable."""
    if origin_id not in nodes or dest_id not in nodes:
        raise KeyError(f"Unknown origin/dest: {origin_id} → {dest_id}")
    avoided = set(avoid_fix_ids or [])
    zones = list(avoid_zones or [])

    dist: dict[str, float] = {origin_id: 0.0}
    prev: dict[str, Optional[str]] = {origin_id: None}
    heap: list[tuple[float, str]] = [(0.0, origin_id)]

    while heap:
        cost_u, u = heappop(heap)
        if cost_u > dist.get(u, math.inf):
            continue
        if u == dest_id:
            break
        for v, edge_d in adj.get(u, []):
            if use_penalties:
                w = edge_cost(
                    edge_d,
                    nodes[u],
                    nodes[v],
                    avoid_fix_ids=avoided,
                    avoid_zones=zones,
                )
            else:
                # ORF-style: pure distance; still skip hard-avoided nodes as waypoints
                if v in avoided and v != dest_id:
                    continue
                w = edge_d
            nd = cost_u + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = u
                heappush(heap, (nd, v))

    if dest_id not in dist:
        raise KeyError(f"No path {origin_id} → {dest_id}")

    path: list[str] = []
    cur: Optional[str] = dest_id
    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)
    path.reverse()

    # Report geometric distance (not penalized cost) for fuel propagator
    geom = 0.0
    for i in range(len(path) - 1):
        geom += haversine_nmi(nodes[path[i]].location, nodes[path[i + 1]].location)
    return path, round(geom, 2)


def route_via_chain(
    nodes: dict[str, GraphNode],
    adj: dict[str, list[tuple[str, float]]],
    origin_id: str,
    dest_id: str,
    vias: list[str],
    *,
    avoid_fix_ids: Optional[Iterable[str]] = None,
    avoid_zones: Optional[list[AvoidZone]] = None,
    use_penalties: bool = False,
) -> tuple[list[str], float]:
    """Shortest path origin → via1 → … → dest, concatenating segments."""
    waypoints = [origin_id, *[v for v in vias if v in nodes], dest_id]
    # Deduplicate consecutive
    compact: list[str] = []
    for w in waypoints:
        if not compact or compact[-1] != w:
            compact.append(w)

    full: list[str] = []
    total = 0.0
    for i in range(len(compact) - 1):
        seg, dist = dijkstra(
            adj,
            nodes,
            compact[i],
            compact[i + 1],
            avoid_fix_ids=avoid_fix_ids,
            avoid_zones=avoid_zones,
            use_penalties=use_penalties,
        )
        if full and seg and full[-1] == seg[0]:
            full.extend(seg[1:])
        else:
            full.extend(seg)
        total += dist
    return full, round(total, 2)


def build_default_graph(
    airbases: dict[str, Airbase],
    navaids: dict[str, Navaid],
    mission_waypoints: Optional[dict[str, PublishedFix]] = None,
) -> tuple[dict[str, GraphNode], dict[str, list[tuple[str, float]]]]:
    nodes = build_nodes(airbases, navaids, mission_waypoints)
    adj = _k_nearest_edges(nodes, k=7, max_link_nmi=500.0)
    return nodes, adj


def covering_fix_ids_for_tasks(
    nodes: dict[str, GraphNode],
    tasks: list,
    *,
    origin_id: str,
    isr_nmi: float = 80.0,
    strike_nmi: float = 20.0,
) -> list[str]:
    """
    Nearest-neighbor order of published fixes that cover each task.

    Used so ORF / cost-grid paths still visit theater fixes that satisfy
    proximity (geometry only — association happens in core).
    """
    from ..models import TaskType

    if origin_id not in nodes:
        return []
    current = nodes[origin_id].location
    remaining = list(tasks)
    ordered: list[str] = []
    while remaining:
        task = min(remaining, key=lambda t: haversine_nmi(current, t.location))
        remaining.remove(task)
        radius = isr_nmi if task.type == TaskType.ISR else strike_nmi
        candidates = [
            n
            for n in nodes.values()
            if haversine_nmi(n.location, task.location) <= radius
        ]
        if not candidates:
            continue
        chosen = min(candidates, key=lambda n: haversine_nmi(current, n.location))
        if not ordered or ordered[-1] != chosen.id:
            ordered.append(chosen.id)
        current = chosen.location
    return ordered
