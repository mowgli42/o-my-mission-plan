"""Simple geographic helpers."""

from __future__ import annotations

import math

from .models import LatLon

NM_PER_DEG_LAT = 60.0  # approximate


def haversine_nmi(a: LatLon, b: LatLon) -> float:
    """Great-circle distance in nautical miles."""
    R_nm = 3440.065  # Earth radius in nmi

    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    dlat = math.radians(b.lat - a.lat)
    dlon = math.radians(b.lon - a.lon)

    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * R_nm * math.asin(math.sqrt(h))
