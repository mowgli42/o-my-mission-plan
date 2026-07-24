"""Map layers: hex cost-grid, threat exposure, multi-platform timeline."""

from __future__ import annotations

import math
from typing import Any, Optional

from .models import Threat
from .options import NOMINAL_CRUISE_KT
from .planning import PlanCycleResult

# "Sees" uses jam radius for soft detection, lethal for hard exposure
SEES_MODE = "jam_or_lethal"


def _haversine_nmi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3440.065  # nmi
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


SEVERITY_WEIGHT = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.5, "CRITICAL": 5.0}


def build_hex_costgrid(
    threats: list[Threat],
    *,
    min_lat: float = 23.5,
    max_lat: float = 34.0,
    min_lon: float = 43.5,
    max_lon: float = 51.5,
    cell_nmi: float = 45.0,
) -> dict[str, Any]:
    """
    Coarse hex-like lattice of cost cells (performant).

    Intensity per cell = max overlapping threat contribution
    (severity weight × falloff inside jam radius). Documented choice: max, not sum.
    """
    # Approximate degrees per nmi
    dlat = cell_nmi / 60.0
    dlon = cell_nmi / (60.0 * max(0.5, math.cos(math.radians((min_lat + max_lat) / 2))))
    cells: list[dict[str, Any]] = []
    row = 0
    lat = min_lat
    while lat <= max_lat:
        lon0 = min_lon + (0.5 * dlon if row % 2 else 0.0)
        lon = lon0
        while lon <= max_lon:
            intensity = 0.0
            level = "NONE"
            for th in threats:
                d = _haversine_nmi(lat, lon, th.location.lat, th.location.lon)
                radius = float(th.jam_radius_nmi or 100.0)
                if d > radius:
                    continue
                w = SEVERITY_WEIGHT.get((th.severity or "MEDIUM").upper(), 2.0)
                contrib = w * (1.0 - d / radius)
                if contrib > intensity:
                    intensity = contrib
                    level = (th.severity or "MEDIUM").upper()
            if intensity > 0:
                # Flat-top hex vertices in lat/lon approx
                rx, ry = dlon * 0.48, dlat * 0.55
                verts = [
                    [lat, lon + rx],
                    [lat + ry * 0.5, lon + rx * 0.5],
                    [lat + ry * 0.5, lon - rx * 0.5],
                    [lat, lon - rx],
                    [lat - ry * 0.5, lon - rx * 0.5],
                    [lat - ry * 0.5, lon + rx * 0.5],
                ]
                cells.append(
                    {
                        "lat": round(lat, 4),
                        "lon": round(lon, 4),
                        "intensity": round(intensity, 3),
                        "level": level,
                        "vertices": [[round(a, 4), round(b, 4)] for a, b in verts],
                    }
                )
            lon += dlon
        lat += dlat * 0.75
        row += 1

    return {
        "cell_nmi": cell_nmi,
        "aggregation": "max",
        "sees_mode_note": (
            "Cost field uses jam-radius soft falloff × severity weight; "
            "pairs with ROUTE_SUPPLIER=costgrid pathing but does not change geometry alone."
        ),
        "levels": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        "cell_count": len(cells),
        "cells": cells,
    }


def leg_exposure(
    threats: list[Threat],
    waypoints: list[Any],
    *,
    samples_per_leg: int = 8,
) -> list[dict[str, Any]]:
    """Per-leg threats that 'see' the platform (jam or lethal intersection)."""
    out: list[dict[str, Any]] = []
    for i in range(len(waypoints) - 1):
        a, b = waypoints[i], waypoints[i + 1]
        alat, alon = a.location.lat, a.location.lon
        blat, blon = b.location.lat, b.location.lon
        seen: list[dict[str, Any]] = []
        for th in threats:
            lethal = float(th.lethal_radius_nmi or 50.0)
            jam = float(th.jam_radius_nmi or 160.0)
            min_d = min(
                _haversine_nmi(
                    alat + (blat - alat) * t,
                    alon + (blon - alon) * t,
                    th.location.lat,
                    th.location.lon,
                )
                for t in [j / samples_per_leg for j in range(samples_per_leg + 1)]
            )
            band = None
            if min_d <= lethal:
                band = "LETHAL"
            elif min_d <= jam:
                band = "JAM"
            if band:
                seen.append(
                    {
                        "threat_id": th.id,
                        "kind": th.kind,
                        "severity": th.severity,
                        "band": band,
                        "closest_nm": round(min_d, 1),
                    }
                )
        out.append(
            {
                "from_id": a.id,
                "to_id": b.id,
                "leg_index": i,
                "exposed": bool(seen),
                "threats": seen,
            }
        )
    return out


def build_exposure_report(
    result: PlanCycleResult,
    threats: list[Threat],
    *,
    aircraft_order: Optional[list[str]] = None,
) -> dict[str, Any]:
    plans = list(result.plans)
    if aircraft_order:
        rank = {aid: i for i, aid in enumerate(aircraft_order)}
        plans = sorted(plans, key=lambda p: rank.get(p.aircraft_id, 999))

    platforms = []
    for p in plans:
        if not p.route or not p.route.waypoints:
            platforms.append(
                {
                    "aircraft_id": p.aircraft_id,
                    "label": p.label,
                    "status": p.status,
                    "legs": [],
                    "threats_that_see": [],
                }
            )
            continue
        legs = leg_exposure(threats, p.route.waypoints)
        seeing = {}
        for leg in legs:
            for t in leg["threats"]:
                seeing[t["threat_id"]] = t
        platforms.append(
            {
                "aircraft_id": p.aircraft_id,
                "label": p.label,
                "status": p.status,
                "legs": legs,
                "threats_that_see": list(seeing.values()),
            }
        )
    return {
        "sees_mode": SEES_MODE,
        "note": (
            "A threat 'sees' a platform when any sampled point on a leg is inside "
            "lethal (hard) or jam (soft) radius — same radii used for costgrid penalties."
        ),
        "platforms": platforms,
    }


def _route_events(plan, cruise_kt: float = NOMINAL_CRUISE_KT) -> dict[str, Any]:
    if not plan.route:
        return {
            "aircraft_id": plan.aircraft_id,
            "label": plan.label,
            "aircraft_type": plan.aircraft_type,
            "status": plan.status,
            "total_minutes": 0.0,
            "events": [],
            "segments": [],
        }
    route = plan.route
    t = 0.0
    events = [
        {
            "t_min": 0.0,
            "kind": "launch",
            "label": f"Launch {plan.label or plan.aircraft_id}",
            "fix_id": route.waypoints[0].id if route.waypoints else None,
        }
    ]
    segments = []
    for i, leg in enumerate(route.legs):
        dur = (leg.distance_nmi / cruise_kt) * 60.0
        segments.append(
            {
                "t0": round(t, 2),
                "t1": round(t + dur, 2),
                "from_id": leg.from_waypoint.id,
                "to_id": leg.to_waypoint.id,
                "distance_nmi": leg.distance_nmi,
            }
        )
        t += dur
        wp = leg.to_waypoint
        kind = "fix"
        label = wp.id
        if wp.associated_task_id:
            tid = wp.associated_task_id
            if tid.startswith("STK"):
                kind = "strike"
                label = f"Strike {tid}"
            elif tid.startswith("ISR"):
                kind = "collect"
                label = f"Collect {tid}"
            else:
                kind = "task"
                label = tid
        events.append(
            {
                "t_min": round(t, 2),
                "kind": kind,
                "label": label,
                "fix_id": wp.id,
                "task_id": wp.associated_task_id,
            }
        )
    return {
        "aircraft_id": plan.aircraft_id,
        "label": plan.label,
        "aircraft_type": plan.aircraft_type,
        "status": plan.status,
        "total_minutes": round(t, 2),
        "total_distance_nmi": route.total_distance_nmi,
        "fuel_margin": (
            None
            if not plan.fuel
            else round(plan.fuel.final_fuel, 1)
        ),
        "events": events,
        "segments": segments,
    }


def build_aligned_timeline(
    result: PlanCycleResult,
    *,
    aircraft_order: Optional[list[str]] = None,
    sync: Optional[dict[str, Any]] = None,
    cruise_kt: float = NOMINAL_CRUISE_KT,
) -> dict[str, Any]:
    plans = list(result.plans)
    if aircraft_order:
        rank = {aid: i for i, aid in enumerate(aircraft_order)}
        plans = sorted(plans, key=lambda p: rank.get(p.aircraft_id, 999))
    tracks = [_route_events(p, cruise_kt) for p in plans]
    max_t = max((tr["total_minutes"] for tr in tracks), default=0.0)
    windows = []
    if sync and sync.get("mean_strike_tot_minutes") is not None:
        mean = float(sync["mean_strike_tot_minutes"])
        windows.append(
            {
                "kind": "tot_band",
                "t0": max(0.0, mean - 7.5),
                "t1": mean + 7.5,
                "label": "TOT window (±7.5m)",
            }
        )
        lag = float(sync.get("bda_lag_minutes") or 30.0)
        windows.append(
            {
                "kind": "bda_lag",
                "t0": mean,
                "t1": mean + lag,
                "label": f"BDA lag {lag:.0f}m",
            }
        )
    return {
        "cruise_kt_assumed": cruise_kt,
        "axis_max_minutes": max_t,
        "sync_windows": windows,
        "tracks": tracks,
        "note": "Shared time axis across platforms in the selected option / latest plan.",
    }


def position_along_route(route, t_min: float, cruise_kt: float = NOMINAL_CRUISE_KT):
    """Interpolate lat/lon at mission time t_min along the route."""
    if not route or not route.waypoints:
        return None
    if t_min <= 0 or not route.legs:
        wp = route.waypoints[0]
        return {"lat": wp.location.lat, "lon": wp.location.lon, "fix_id": wp.id}
    elapsed = 0.0
    for leg in route.legs:
        dur = (leg.distance_nmi / cruise_kt) * 60.0
        if elapsed + dur >= t_min:
            frac = (t_min - elapsed) / dur if dur > 0 else 0.0
            frac = max(0.0, min(1.0, frac))
            a, b = leg.from_waypoint, leg.to_waypoint
            return {
                "lat": a.location.lat + (b.location.lat - a.location.lat) * frac,
                "lon": a.location.lon + (b.location.lon - a.location.lon) * frac,
                "from_id": a.id,
                "to_id": b.id,
            }
        elapsed += dur
    wp = route.waypoints[-1]
    return {"lat": wp.location.lat, "lon": wp.location.lon, "fix_id": wp.id}
