"""Vercel Python entrypoint — re-exports the FastAPI app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
os.environ.setdefault("OMY_MISSION_PLAN_ROOT", str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from omy_mission_plan.app import app  # noqa: E402

__all__ = ["app"]
