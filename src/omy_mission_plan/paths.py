"""Resolve repo-root paths for fixtures and data on local dev and Vercel."""

from __future__ import annotations

import os
from pathlib import Path

GULF_THREATS_MARKER = Path("fixtures/regions/gulf_threats.json")


def find_repo_root() -> Path:
    """Return the directory that contains bundled fixtures (repo root on Vercel)."""
    here = Path(__file__).resolve()
    env_roots = [
        os.environ.get("OMY_MISSION_PLAN_ROOT", "").strip(),
        os.environ.get("VERCEL_PROJECT_ROOT", "").strip(),
    ]
    candidates: list[Path] = []
    for value in env_roots:
        if value:
            candidates.append(Path(value))
    candidates.extend(
        [
            here.parents[2],  # src/omy_mission_plan/paths.py → repo (editable install)
            here.parents[1],
            Path.cwd(),
        ]
    )
    for candidate in candidates:
        if candidate.is_dir() and (candidate / GULF_THREATS_MARKER).is_file():
            return candidate
    return here.parents[2]
