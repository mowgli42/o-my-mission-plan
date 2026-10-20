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


def _cell_vertices(
    lat: float,
    lon: float,
    dlat: float,
    dlon: float,
    *,
    cell_style: str,
) -> list[list[float]]:
    """Edge-to-edge cell polygon in [lat, lon] pairs.

    ``dlat``/``dlon`` are the centre spacings. Squares use exact half-spacings;
    pointy-top hexagons use the matching hex tiling (centre spacing
    ``sqrt(3) * rx`` horizontally and ``1.5 * ry`` vertically), so neighbours
    share edges with neither gaps nor overlaps.
    """
    style = (cell_style or "hex").lower()
    if style == "square":
        hx, hy = dlon * 0.5, dlat * 0.5
        return [
            [lat - hy, lon - hx],
            [lat - hy, lon + hx],
            [lat + hy, lon + hx],
            [lat + hy, lon - hx],
        ]
    rx, ry = dlon / math.sqrt(3.0), dlat / 1.5
    return [
        [lat + ry, lon],
        [lat + ry * 0.5, lon + rx],
        [lat - ry * 0.5, lon + rx],
        [lat - ry, lon],
        [lat - ry * 0.5, lon - rx],
        [lat + ry * 0.5, lon - rx],
    ]


def _level_for_intensity(intensity: float) -> str:
    """Intensity ramp level (not the contributing threat's severity label)."""
    if intensity >= 3.25:
        return "CRITICAL"
    if intensity >= 2.0:
        return "HIGH"
    if intensity >= 0.9:
        return "MEDIUM"
    return "LOW"


# Default PSAB → Kuwait/Iraq theater when no threats are loaded.
DEFAULT_FIELD_BOUNDS = {
    "min_lat": 23.5,
    "max_lat": 34.0,
    "min_lon": 43.5,
    "max_lon": 51.5,
}


def _normalize_frequency_band(value: Optional[str]) -> Optional[str]:
    """Return a filter band, or None for the all-up overlay."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"all", "*", "any"}:
        return None
    return text


def available_frequency_bands(threats: list[Threat]) -> list[str]:
    """Sorted unique RF frequency bands present on the threat set."""
    bands = {str(th.frequency_band).strip() for th in threats if th.frequency_band}
    return sorted(bands)


def filter_threats_by_frequency_band(
    threats: list[Threat],
    frequency_band: Optional[str],
) -> list[Threat]:
    """Keep threats whose RF frequency band matches, or all when unfiltered."""
    band = _normalize_frequency_band(frequency_band)
    if band is None:
        return list(threats)
    return [th for th in threats if str(th.frequency_band or "").strip() == band]


def field_bounds_for_threats(
    threats: list[Threat],
    *,
    padding_nmi: float = 80.0,
    floor: Optional[dict[str, float]] = None,
) -> dict[str, float]:
    """Bounds that fully enclose each threat's jam disc plus padding.

    The previous fixed max_lat=34 clipped Baghdad / northern Iraq jam radii.
    Bounds always expand from the PSAB theater floor so southern approaches
    remain in frame. Extra padding past the jam radius keeps the outer green
    ring fully inside the lattice so discs read as surrounding arcs instead of
    a hard northern clip line.
    """
    base = dict(floor or DEFAULT_FIELD_BOUNDS)
    if not threats:
        return base

    min_lat = base["min_lat"]
    max_lat = base["max_lat"]
    min_lon = base["min_lon"]
    max_lon = base["max_lon"]

    for th in threats:
        radius = float(th.jam_radius_nmi or 100.0) + padding_nmi
        # Degrees: 1° lat ≈ 60 nmi; lon shrinks by cos(lat).
        dlat = radius / 60.0
        cos_lat = max(0.35, math.cos(math.radians(th.location.lat)))
        dlon = radius / (60.0 * cos_lat)
        min_lat = min(min_lat, th.location.lat - dlat)
        max_lat = max(max_lat, th.location.lat + dlat)
        min_lon = min(min_lon, th.location.lon - dlon)
        max_lon = max(max_lon, th.location.lon + dlon)

    return {
        "min_lat": round(min_lat, 4),
        "max_lat": round(max_lat, 4),
        "min_lon": round(min_lon, 4),
        "max_lon": round(max_lon, 4),
    }


def build_hex_costgrid(
    threats: list[Threat],
    *,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    cell_nmi: float = 45.0,
    cell_style: str = "hex",
    altitude_ft: Optional[float] = None,
    frequency_band: Optional[str] = None,
) -> dict[str, Any]:
    """
    Coarse lattice of cost cells (performant hex or square).

    Intensity per cell = max overlapping threat contribution
    (severity weight × falloff inside jam radius). Documented choice: max, not sum.

    Bounds default to every active threat's jam disc so northern Iraq weather
    is not clipped. ``frequency_band`` selects one RF band; omit / ``all`` for
    the composite all-up overlay.

    altitude_ft is display-contract metadata only until stacked layers exist;
    the 2-D field does not yet vary by altitude.
    """
    style = (cell_style or "hex").lower()
    if style not in ("hex", "square"):
        style = "hex"

    all_bands = available_frequency_bands(threats)
    band_filter = _normalize_frequency_band(frequency_band)
    active = filter_threats_by_frequency_band(threats, band_filter)

    explicit = None not in (min_lat, max_lat, min_lon, max_lon)
    if explicit:
        bounds = {
            "min_lat": float(min_lat),
            "max_lat": float(max_lat),
            "min_lon": float(min_lon),
            "max_lon": float(max_lon),
        }
    else:
        # Bounds from the full threat set so switching bands does not jump the
        # theater frame; intensity still uses only the active band.
        bounds = field_bounds_for_threats(threats)

    min_lat_v = bounds["min_lat"]
    max_lat_v = bounds["max_lat"]
    min_lon_v = bounds["min_lon"]
    max_lon_v = bounds["max_lon"]

    # The operator-facing cell-size control stays as selected. Rendering
    # samples the same supplier formula on a half-pitch lattice so adjacent
    # covered cells form continuous regional zones at demo scale.
    render_cell_nmi = cell_nmi / 2.0
    # Approximate degrees per nmi
    dlat = render_cell_nmi / 60.0
    dlon = render_cell_nmi / (
        60.0 * max(0.5, math.cos(math.radians((min_lat_v + max_lat_v) / 2)))
    )
    cells: list[dict[str, Any]] = []
    row = 0
    lat = min_lat_v
    lat_step = dlat
    while lat <= max_lat_v:
        lon0 = min_lon_v + (0.5 * dlon if (style == "hex" and row % 2) else 0.0)
        lon = lon0
        while lon <= max_lon_v:
            intensity = 0.0
            for th in active:
                d = _haversine_nmi(lat, lon, th.location.lat, th.location.lon)
                radius = float(th.jam_radius_nmi or 100.0)
                if d > radius:
                    continue
                w = SEVERITY_WEIGHT.get((th.severity or "MEDIUM").upper(), 2.0)
                contrib = w * (1.0 - d / radius)
                if contrib > intensity:
                    intensity = contrib
            if intensity > 0:
                verts = _cell_vertices(lat, lon, dlat, dlon, cell_style=style)
                cells.append(
                    {
                        "lat": round(lat, 4),
                        "lon": round(lon, 4),
                        "intensity": round(intensity, 3),
                        "level": _level_for_intensity(intensity),
                        "vertices": [[round(a, 4), round(b, 4)] for a, b in verts],
                    }
                )
            lon += dlon
        lat += lat_step
        row += 1

    return {
        "cell_nmi": cell_nmi,
        "render_cell_nmi": render_cell_nmi,
        "tiling": "edge-to-edge",
        "cell_style": style,
        "altitude_ft": altitude_ft,
        "altitude_note": (
            "Display-only altitude selector; field is still a single 2-D layer "
            "until Option B stacked layers are implemented."
        ),
        "aggregation": "max",
        "aggregation_note": (
            "Intensity = max overlapping threat contribution "
            "(severity weight × jam-radius falloff), not sum."
        ),
        "sees_mode_note": (
            "Cost field uses jam-radius soft falloff × severity weight; "
            "pairs with ROUTE_SUPPLIER=costgrid pathing but does not change geometry alone."
        ),
        "frequency_band": band_filter or "all",
        "available_frequency_bands": all_bands,
        "threat_count": len(active),
        "threat_count_all": len(threats),
        "bounds": bounds,
        "bounds_note": (
            "Field bounds expand to enclose every threat jam disc so weather "
            "is not clipped in northern Iraq / Mosul."
        ),
        "levels": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        "color_ramp": {
            "LOW": "#2ecc71",
            "MEDIUM": "#f1c40f",
            "HIGH": "#e67e22",
            "CRITICAL": "#e74c3c",
        },
        "cell_count": len(cells),
        "cells": cells,
    }


def _exposure_at(distance_nmi: float, threat: Threat) -> str:
    """Route-exposure state at one route point for one threat."""
    if distance_nmi <= float(threat.lethal_radius_nmi or 50.0):
        return "LETHAL"
    if distance_nmi <= float(threat.jam_radius_nmi or 160.0):
        return "JAMMED"
    return "CLEAR"


_EXPOSURE_RANK = {"CLEAR": 0, "JAMMED": 1, "LETHAL": 2}


def _route_point(a: Any, b: Any, fraction: float) -> dict[str, float]:
    return {
        "lat": round(a.location.lat + (b.location.lat - a.location.lat) * fraction, 5),
        "lon": round(a.location.lon + (b.location.lon - a.location.lon) * fraction, 5),
    }


def leg_exposure(
    threats: list[Threat],
    waypoints: list[Any],
    *,
    sample_step_nmi: float = 2.0,
) -> list[dict[str, Any]]:
    """Point/sub-segment exposure for each leg.

    A leg is never classified as a single wash. It is sampled at roughly
    ``sample_step_nmi`` intervals; consecutive samples with the same worst
    exposure are merged into short ``exposure_spans`` with exact route
    endpoints. Per-threat spans are retained so selecting one threat can show
    only its affected sub-segments.
    """
    out: list[dict[str, Any]] = []
    for i in range(len(waypoints) - 1):
        a, b = waypoints[i], waypoints[i + 1]
        leg_length = _haversine_nmi(
            a.location.lat, a.location.lon, b.location.lat, b.location.lon
        )
        sample_count = max(16, min(160, math.ceil(leg_length / max(sample_step_nmi, 0.5))))
        # Per-sample classification: aggregate worst state + per-threat state.
        samples: list[dict[str, Any]] = []
        for j in range(sample_count + 1):
            fraction = j / sample_count
            point = _route_point(a, b, fraction)
            per_threat: dict[str, tuple[str, float]] = {}
            worst = "CLEAR"
            for th in threats:
                distance = _haversine_nmi(
                    point["lat"], point["lon"], th.location.lat, th.location.lon
                )
                exposure = _exposure_at(distance, th)
                per_threat[th.id] = (exposure, distance)
                if _EXPOSURE_RANK[exposure] > _EXPOSURE_RANK[worst]:
                    worst = exposure
            samples.append(
                {
                    "fraction": fraction,
                    "point": point,
                    "exposure": worst,
                    "per_threat": per_threat,
                }
            )

        # Intervals between sample points, classified at their midpoint.
        intervals: list[dict[str, Any]] = []
        for j in range(sample_count):
            from_fraction = j / sample_count
            to_fraction = (j + 1) / sample_count
            midpoint = _route_point(a, b, (from_fraction + to_fraction) / 2)
            per_threat: dict[str, tuple[str, float]] = {}
            worst = "CLEAR"
            for th in threats:
                distance = _haversine_nmi(
                    midpoint["lat"], midpoint["lon"], th.location.lat, th.location.lon
                )
                exposure = _exposure_at(distance, th)
                per_threat[th.id] = (exposure, distance)
                if _EXPOSURE_RANK[exposure] > _EXPOSURE_RANK[worst]:
                    worst = exposure
            intervals.append(
                {
                    "from_fraction": from_fraction,
                    "to_fraction": to_fraction,
                    "exposure": worst,
                    "per_threat": per_threat,
                }
            )

        # Aggregate spans (worst state across threats on each interval).
        exposure_spans: list[dict[str, Any]] = []
        start = 0
        for j in range(1, len(intervals) + 1):
            current = intervals[start]["exposure"]
            if j < len(intervals) and intervals[j]["exposure"] == current:
                continue
            if current != "CLEAR":
                midpoint = intervals[(start + j - 1) // 2]
                exposure_spans.append(
                    {
                        "leg_index": i,
                        "from_fraction": round(intervals[start]["from_fraction"], 5),
                        "to_fraction": round(intervals[j - 1]["to_fraction"], 5),
                        "from": _route_point(a, b, intervals[start]["from_fraction"]),
                        "to": _route_point(a, b, intervals[j - 1]["to_fraction"]),
                        "exposure": current,
                        "threat_ids": [
                            threat_id
                            for threat_id, (state, _d) in midpoint["per_threat"].items()
                            if state != "CLEAR"
                        ],
                    }
                )
            start = j

        seen: list[dict[str, Any]] = []
        impacted_points: list[dict[str, Any]] = []
        for sample in samples:
            if sample["exposure"] == "CLEAR":
                continue
            # Keep route vertices and span boundaries as explicit points;
            # span endpoints are added below, vertices are fractions 0/1.
            if sample["fraction"] in (0.0, 1.0):
                impacted_points.append(
                    {
                        **sample["point"],
                        "leg_index": i,
                        "fraction": round(sample["fraction"], 5),
                        "exposure": sample["exposure"],
                        "threat_ids": [
                            threat_id
                            for threat_id, (state, _d) in sample["per_threat"].items()
                            if state != "CLEAR"
                        ],
                    }
                )
        for span in exposure_spans:
            for key in ("from", "to"):
                impacted_points.append(
                    {
                        **span[key],
                        "leg_index": i,
                        "fraction": span["from_fraction"] if key == "from" else span["to_fraction"],
                        "exposure": span["exposure"],
                        "threat_ids": list(span["threat_ids"]),
                    }
                )

        for th in threats:
            states = [sample["per_threat"][th.id] for sample in samples]
            exposed_states = [(state, dist) for state, dist in states if state != "CLEAR"]
            if not exposed_states:
                continue
            worst = max((state for state, _d in exposed_states), key=_EXPOSURE_RANK.get)
            threat_spans: list[dict[str, Any]] = []
            start = 0
            for j in range(1, len(intervals) + 1):
                current = intervals[start]["per_threat"][th.id][0]
                if j < len(intervals) and intervals[j]["per_threat"][th.id][0] == current:
                    continue
                if current != "CLEAR":
                    threat_spans.append(
                        {
                            "leg_index": i,
                            "from_fraction": round(intervals[start]["from_fraction"], 5),
                            "to_fraction": round(intervals[j - 1]["to_fraction"], 5),
                            "from": _route_point(a, b, intervals[start]["from_fraction"]),
                            "to": _route_point(a, b, intervals[j - 1]["to_fraction"]),
                            "exposure": current,
                            "threat_ids": [th.id],
                        }
                    )
                start = j
            seen.append(
                {
                    "threat_id": th.id,
                    "kind": th.kind,
                    "severity": th.severity,
                    "frequency_band": th.frequency_band,
                    "exposure": worst,
                    "closest_nm": round(min(dist for _s, dist in states), 1),
                    "spans": threat_spans,
                }
            )

        out.append(
            {
                "from_id": a.id,
                "to_id": b.id,
                "leg_index": i,
                "exposed": bool(exposure_spans),
                "worst_exposure": max(
                    (span["exposure"] for span in exposure_spans),
                    key=_EXPOSURE_RANK.get,
                    default="CLEAR",
                ),
                "exposure_spans": exposure_spans,
                "impacted_points": impacted_points,
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
        seeing: dict[str, dict[str, Any]] = {}
        for leg in legs:
            for t in leg["threats"]:
                existing = seeing.get(t["threat_id"])
                if existing is None:
                    seeing[t["threat_id"]] = {**t, "spans": list(t.get("spans") or [])}
                    continue
                existing["spans"].extend(t.get("spans") or [])
                existing["closest_nm"] = min(existing["closest_nm"], t["closest_nm"])
                if _EXPOSURE_RANK[t["exposure"]] > _EXPOSURE_RANK[existing["exposure"]]:
                    existing["exposure"] = t["exposure"]
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
            "A threat 'sees' a platform when a sampled route point or sub-segment is inside "
            "its lethal (hard) or jammed (soft) radius — same radii used for costgrid penalties. "
            "Exposure states are clear / jammed / lethal; frequency_band is the threat's RF band."
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
                "kind": "tot_window",
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
