Feature: o-my Mission Planning
  As a mission planner (or automated process)
  I want to allocate tasks to aircraft, generate feasible routes using commercial navaids,
  and check fuel feasibility so that I can iterate quickly on “what is possible”.

  Background:
    Given a demo world with Central/East Florida airbases and commercial navaids
    And a set of aircraft (ISR, fighter, bomber) each with a home airbase and fuel model
    And a pool of unassigned ISR and strike tasks

  Scenario: Simple regional allocation and initial route
    When the allocator groups tasks by region and assigns them to suitable aircraft
    And the route generator builds an ordered route for each assigned aircraft
    Then each route starts and ends at the aircraft’s home airbase
    And ISR routes use approximately 80 nmi legs between points
    And strike routes use approximately 20 nmi legs between points
    And the route uses commercial navaid identifiers as waypoints where appropriate

  Scenario: Fuel feasibility check via Route Propagation Service
    Given an aircraft with an initial route and starting fuel
    When the Route Propagation Service computes fuel remaining after each leg
    Then it reports remaining fuel per leg
    And it reports overall feasibility (can complete with reserves)

  Scenario: Dynamic task insertion during execution
    Given an aircraft that is already flying an assigned route
    When a new high-priority strike task is identified in the same region
    And the task is injected into the aircraft’s plan
    Then the route is updated to include the new task
    And fuel is re-propagated
    And a new feasibility result is returned
