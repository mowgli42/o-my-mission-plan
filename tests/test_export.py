from omy_mission_plan.demo_world import AIRCRAFT, LAUNCH_BASE_ID, SCENARIO_ID
from omy_mission_plan.export_routes import SCHEMA_ID, build_export_bundle
from omy_mission_plan.planning import PlanningSession


def test_build_export_bundle_schema():
    session = PlanningSession()
    plan = session.run_plan_cycle()
    bundle = build_export_bundle(plan, AIRCRAFT)
    assert bundle["schema"] == SCHEMA_ID
    assert bundle["scenario_id"] == SCENARIO_ID
    assert bundle["launch_base_id"] == LAUNCH_BASE_ID
    assert all(r["launch"]["publish"] for r in bundle["routes"])
    assert all(r["uci_topic"] == "uci.route" for r in bundle["routes"])
