"""Tests for repo-root path resolution (local + Vercel bundles)."""

from __future__ import annotations

import os
from pathlib import Path

from omy_mission_plan.paths import find_repo_root
from omy_mission_plan.region_threats import default_fixture_path


def test_default_fixture_exists_in_repo():
    fixture = default_fixture_path()
    assert fixture.is_file(), fixture
    assert fixture.name == "gulf_threats.json"


def test_find_repo_root_honors_env_override(monkeypatch, tmp_path: Path):
    bundled = tmp_path / "fixtures" / "regions"
    bundled.mkdir(parents=True)
    (bundled / "gulf_threats.json").write_text('{"entities": []}', encoding="utf-8")
    monkeypatch.setenv("OMY_MISSION_PLAN_ROOT", str(tmp_path))
    assert find_repo_root() == tmp_path
    assert default_fixture_path() == bundled / "gulf_threats.json"
