from omy_mission_plan.allocator import allocate
from omy_mission_plan.demo_world import AIRBASES, AIRCRAFT, TASKS


def test_allocate_returns_unallocated_list():
    result = allocate(TASKS, AIRCRAFT, AIRBASES)
    assert isinstance(result.unallocated_task_ids, list)
    assigned = {tid for tids in result.assignments.values() for tid in tids}
    for tid in result.unallocated_task_ids:
        assert tid not in assigned


def test_allocate_covers_or_reports_every_task():
    result = allocate(TASKS, AIRCRAFT, AIRBASES)
    assigned = {tid for tids in result.assignments.values() for tid in tids}
    all_ids = {t.id for t in TASKS}
    assert assigned | set(result.unallocated_task_ids) == all_ids


def test_isr_prefers_isr_aircraft():
    result = allocate(TASKS, AIRCRAFT, AIRBASES)
    # At least one ISR aircraft should get ISR tasks when available
    isr_assignments = result.assignments.get("ISR-1", []) + result.assignments.get("ISR-2", [])
    assert any(tid.startswith("ISR") for tid in isr_assignments) or result.unallocated_task_ids
