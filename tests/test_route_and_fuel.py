from omy_mission_plan.demo_world import (
    AIRBASES,
    AIRCRAFT,
    MISSION_WAYPOINTS,
    NAVAIDS,
    TASKS,
    get_airbase,
)
from omy_mission_plan.propagator import propagate
from omy_mission_plan.route_generator import (
    ISR_PROXIMITY_NMI,
    STRIKE_PROXIMITY_NMI,
    assert_published_only,
    generate_route,
    proximity_for,
    route_satisfies_proximity,
)
from omy_mission_plan.geo import haversine_nmi
from omy_mission_plan.models import LatLon, Task, TaskType


def _route(ac, tasks):
    return generate_route(
        ac,
        tasks,
        get_airbase(ac),
        NAVAIDS,
        airbases=AIRBASES,
        mission_waypoints=MISSION_WAYPOINTS,
    )


def test_all_aircraft_launch_from_psab():
    assert all(a.home_base_id == "OEPS" for a in AIRCRAFT)
    assert "OEPS" in AIRBASES


def test_route_starts_and_ends_at_home():
    ac = AIRCRAFT[0]
    tasks = [t for t in TASKS if t.type == TaskType.ISR][:2]
    home = get_airbase(ac)
    route = _route(ac, tasks)
    assert route.waypoints[0].kind == "airbase"
    assert route.waypoints[-1].kind == "airbase"
    assert route.waypoints[0].id == home.id
    assert route.waypoints[-1].id == home.id


def test_route_uses_only_published_waypoints():
    ac = next(a for a in AIRCRAFT if a.type.value == "FIGHTER")
    route = _route(ac, TASKS[:4])
    assert_published_only(route)
    for wp in route.waypoints:
        assert not wp.id.startswith("PROX-")
        assert wp.kind in {"airbase", "navaid", "mission"}


def test_route_respects_proximity_via_published_fixes():
    ac = next(a for a in AIRCRAFT if a.type.value == "FIGHTER")
    tasks = [t for t in TASKS if t.type == TaskType.STRIKE][:2]
    route = _route(ac, tasks)
    assert route.unsatisfied_task_ids == []
    assert route_satisfies_proximity(route, tasks)
    # Should visit theater mission fixes, not invent PROX points
    kinds = {wp.kind for wp in route.waypoints}
    assert "mission" in kinds or "navaid" in kinds or "airbase" in kinds
    for task in tasks:
        radius = proximity_for(task)
        assert radius in (ISR_PROXIMITY_NMI, STRIKE_PROXIMITY_NMI)
        assert any(
            haversine_nmi(wp.location, task.location) <= radius for wp in route.waypoints
        )


def test_unsatisfied_when_no_published_fix_in_range():
    ac = AIRCRAFT[0]
    far = Task(
        id="STK-FAR",
        type=TaskType.STRIKE,
        location=LatLon(lat=10.0, lon=10.0),
        priority=1,
        label="Far strike outside published coverage",
    )
    route = _route(ac, [far])
    assert "STK-FAR" in route.unsatisfied_task_ids
    assert_published_only(route)


def test_fuel_feasibility_go():
    ac = AIRCRAFT[0]
    tasks = [TASKS[0]]
    route = _route(ac, tasks)
    route, fuel = propagate(route, ac)
    assert fuel.feasible is True
    assert route.feasible is True
    assert fuel.final_fuel >= ac.reserve_fuel


def test_fuel_feasibility_nogo_when_reserve_impossible():
    ac = AIRCRAFT[0].model_copy(update={"reserve_fuel": 1e9})
    tasks = TASKS[:2]
    route = _route(ac, tasks)
    route, fuel = propagate(route, ac)
    assert fuel.feasible is False
    assert route.feasible is False
    assert "fuel" in (fuel.infeasible_reason or "").lower()
