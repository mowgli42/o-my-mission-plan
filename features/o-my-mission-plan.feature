Feature: o-my Mission Planning
  As a mission planner (or automated process)
  I want to allocate tasks to aircraft, generate feasible routes using commercial navaids,
  and check fuel feasibility so that I can iterate quickly on “what is possible”.

  Background:
    Given a demo world with Central/East Florida airbases and commercial navaids
    And 2 ISR, 3 fighter, and 2 bomber aircraft each with a home airbase, constant burn rate, and fixed reserve
    And a pool of unassigned ISR and strike tasks (approximately 4–5 ISR and 2–3 strike)

  Scenario: Simple regional allocation with unallocated feedback
    When the allocator groups tasks by region and assigns them to suitable aircraft
    Then each assigned group is given to a capable aircraft
    And any tasks that could not be allocated are explicitly reported

  Scenario: Initial route respects proximity rules
    Given an aircraft with one or more assigned tasks
    When the route generator builds an ordered route
    Then the route starts and ends at the aircraft’s home airbase
    And the route uses commercial navaid identifiers as waypoints where appropriate
    And the aircraft comes within 80 nmi of every assigned ISR task
    And the aircraft comes within 20 nmi of every assigned strike task
    And individual legs may be longer than the proximity distances as needed

  Scenario: Fuel feasibility check via Route Propagation Service
    Given an aircraft with an initial route and starting fuel
    When the Route Propagation Service computes fuel remaining after each leg using constant burn rate
    Then it reports remaining fuel per leg
    And it reports overall feasibility (GO if end fuel ≥ fixed reserve, otherwise NO-GO / unexecutable)
    And unexecutable routes due to fuel constraints are clearly flagged

  Scenario: Dynamic task insertion forces full re-assessment
    Given an aircraft that already has an assigned route
    When a new strike task is identified and injected into the aircraft’s plan
    Then the entire route is re-generated / re-assessed to include the new task
    And fuel is fully re-propagated
    And a new feasibility result (GO or NO-GO) is returned
