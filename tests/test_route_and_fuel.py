from omy_mission_plan.demo_world import AIRBASES, AIRCRAFT, NAVAIDS, TASKS, get_airbase
from omy_mission_plan.propagator import propagate
from omy_mission_plan.route_generator import (
    ISR_PROXIMITY_NMI,
    STRIKE_PROXIMITY_NMI,
    generate_route,
    proximity_for,
    route_satisfies_proximity,
)
from omy_mission_plan.geo import haversine_nmi
from omy_mission_plan.models import TaskType


def test_route_starts_and_ends_at_home():
    ac = AIRCRAFT[0]
    tasks = [t for t in TASKS if t.type == TaskType.ISR][:2]
    home = get_airbase(ac)
    route = generate_route(ac, tasks, home, NAVAIDS)
    assert route.waypoints[0].kind == "airbase"
    assert route.waypoints[-1].kind == "airbase"
    assert abs(route.waypoints[0].location.lat - home.location.lat) < 1e-6
    assert abs(route.waypoints[-1].location.lat - home.location.lat) < 1e-6


def test_route_respects_proximity():
    ac = next(a for a in AIRCRAFT if a.type.value == "FIGHTER")
    tasks = TASKS[:3]
    home = get_airbase(ac)
    route = generate_route(ac, tasks, home, NAVAIDS)
    assert route_satisfies_proximity(route, tasks)
    for task in tasks:
        radius = proximity_for(task)
        assert radius in (ISR_PROXIMITY_NMI, STRIKE_PROXIMITY_NMI)
        assert any(haversine_nmi(wp.location, task.location) <= radius for wp in route.waypoints)


def test_fuel_feasibility_go():
    ac = AIRCRAFT[0]
    tasks = [TASKS[0]]
    route = generate_route(ac, tasks, get_airbase(ac), NAVAIDS)
    route, fuel = propagate(route, ac)
    assert fuel.feasible is True
    assert route.feasible is True
    assert fuel.final_fuel >= ac.reserve_fuel


def test_fuel_feasibility_nogo_when_reserve_impossible():
    ac = AIRCRAFT[0].model_copy(update={"reserve_fuel": 1e9})
    tasks = TASKS[:2]
    route = generate_route(ac, tasks, get_airbase(ac), NAVAIDS)
    route, fuel = propagate(route, ac)
    assert fuel.feasible is False
    assert route.feasible is False
    assert "fuel" in (fuel.infeasible_reason or "").lower()
