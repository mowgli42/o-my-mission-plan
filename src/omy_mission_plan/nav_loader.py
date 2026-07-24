"""Theater navigation database loader — fixtures or X-Plane earth_nav extract.

See docs/NAV-DATA.md. Config: NAV_SOURCE=fixture|xplane
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from . import demo_world
from .models import Airbase, LatLon, Navaid
from .route_generator import PublishedFix

# Gulf / PSAB theater bbox (slightly padded)
DEFAULT_BBOX = {
    "min_lat": 22.0,
    "max_lat": 35.0,
    "min_lon": 42.0,
    "max_lon": 52.5,
}

# Default extract shipped with the repo (small, demo-scale — not full global)
DEFAULT_XPLANE_EXTRACT = (
    Path(__file__).resolve().parents[2] / "data" / "nav" / "gulf-earth_nav.dat"
)


def configured_nav_source() -> str:
    return os.environ.get("NAV_SOURCE", "fixture").strip().lower() or "fixture"


def xplane_data_path() -> Path:
    override = os.environ.get("XPLANE_NAV_PATH", "").strip()
    if override:
        return Path(override)
    return DEFAULT_XPLANE_EXTRACT


def _in_bbox(lat: float, lon: float, bbox: dict) -> bool:
    return (
        bbox["min_lat"] <= lat <= bbox["max_lat"]
        and bbox["min_lon"] <= lon <= bbox["max_lon"]
    )


def parse_earth_nav_dat(
    path: Path,
    *,
    bbox: Optional[dict] = None,
) -> dict[str, Navaid]:
    """
    Parse a subset of X-Plane earth_nav.dat (types 2=VOR, 3=NDB, 13=DME).

    Format reference: X-Plane 11+ earth_nav.dat row layout
    (type lat lon elev freq ... ident name). Attribution: see docs/NAV-DATA.md.
    """
    bbox = bbox or DEFAULT_BBOX
    navaids: dict[str, Navaid] = {}
    if not path.is_file():
        return navaids

    type_map = {2: "VOR", 3: "NDB", 13: "DME", 5: "LOC"}
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("I") or line.startswith("99"):
            continue
        if line.startswith("#") or line.lower().startswith("copyright"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        try:
            row_type = int(parts[0])
        except ValueError:
            continue
        if row_type not in type_map:
            continue
        try:
            lat = float(parts[1])
            lon = float(parts[2])
        except ValueError:
            continue
        if not _in_bbox(lat, lon, bbox):
            continue
        # X-Plane: ident is typically near the end before the name tokens.
        # Simplified extract format we ship:
        # type lat lon elev freq class BFO ident name...
        ident = parts[7].upper() if len(parts) > 7 else None
        if not ident or len(ident) > 6:
            # try alternate column
            ident = parts[8].upper() if len(parts) > 8 else f"NAV{len(navaids)}"
        name = " ".join(parts[8:]) if len(parts) > 8 else ident
        # Avoid colliding with airbase ids
        nid = ident
        if nid in navaids:
            nid = f"{ident}-{row_type}"
        navaids[nid] = Navaid(
            id=nid,
            name=name.strip() or nid,
            location=LatLon(lat=lat, lon=lon),
            navaid_type=type_map[row_type],
        )
    return navaids


def load_nav_database(
    *,
    source: Optional[str] = None,
    bbox: Optional[dict] = None,
) -> dict[str, object]:
    """
    Return airbases, navaids, mission_waypoints for the planning session.

    Always starts from fixture airbases + mission waypoints. Navaids are either
    fixtures only, or fixtures merged with X-Plane extract (extract wins on id).
    """
    src = (source or configured_nav_source()).lower()
    airbases: dict[str, Airbase] = dict(demo_world.AIRBASES)
    mission_waypoints: dict[str, PublishedFix] = dict(demo_world.MISSION_WAYPOINTS)
    navaids: dict[str, Navaid] = dict(demo_world.NAVAIDS)
    notes: list[str] = [f"NAV_SOURCE={src}"]

    if src in {"xplane", "xp", "earth_nav"}:
        path = xplane_data_path()
        if path.is_file():
            loaded = parse_earth_nav_dat(path, bbox=bbox or DEFAULT_BBOX)
            # Merge: keep fixture keys, add / overlay extract denser set
            for nid, nav in loaded.items():
                navaids[nid] = nav
            notes.append(f"Loaded {len(loaded)} fixes from {path.name} (bbox-filtered)")
            notes.append(f"Published navaid count: {len(navaids)}")
        else:
            notes.append(
                f"X-Plane extract missing at {path}; using fixture navaids only"
            )
            src = "fixture"
    else:
        notes.append(f"Fixture navaids: {len(navaids)}")

    return {
        "source": src if src in {"xplane", "xp", "earth_nav"} else "fixture",
        "airbases": airbases,
        "navaids": navaids,
        "mission_waypoints": mission_waypoints,
        "notes": notes,
        "navaid_count": len(navaids),
        "path": str(xplane_data_path()) if src != "fixture" else None,
    }
