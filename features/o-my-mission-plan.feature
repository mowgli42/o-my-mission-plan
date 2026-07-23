Feature: o-my Mission Planning
  As a mission planner (or automated process)
  I want to allocate tasks to aircraft launched from PSAB, generate feasible routes
  using published waypoints across Kuwait and Iraq, check fuel feasibility, and
  export final routes so o-my-sim can publish them on aircraft launch.

  Background:
    Given a Gulf War demo world with launch base OEPS (Prince Sultan AB / PSAB)
    And published airbases, commercial navaids, and fixed mission waypoints in Kuwait / Iraq
    And 2 ISR, 3 fighter, and 2 bomber aircraft all home-based at OEPS
    And a pool of unassigned ISR and strike tasks across Kuwait and Iraq

  Scenario: Simple regional allocation with unallocated feedback
    When the allocator groups tasks by region and assigns them to suitable aircraft
    Then each assigned group is given to a capable aircraft
    And any tasks that could not be allocated are explicitly reported

  Scenario: Initial route uses published waypoints that satisfy proximity
    Given an aircraft with one or more assigned tasks
    When the route generator builds an ordered route
    Then the route starts and ends at the aircraft’s home airbase (OEPS)
    And the route is a sequence of published waypoints only (airbases, commercial navaids, optional fixed mission waypoints)
    And no runtime-invented proximity points (PROX-*) appear
    And at least one published waypoint lies within 80 nmi of every assigned ISR task that can be satisfied
    And at least one published waypoint lies within 20 nmi of every assigned strike task that can be satisfied
    And tasks that cannot be satisfied by any published fix are explicitly reported
    And individual legs are great-circle between consecutive published waypoints (any length)

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

  Scenario: Final GO routes are exported for o-my-sim
    Given a completed plan cycle with one or more GO routes
    When the planner exports routes for simulation
    Then a JSON bundle with schema o-my.mission-plan.routes/v1 is produced
    And each GO route lists ordered published waypoints starting and ending at OEPS
    And each route is marked for publish on uci.route when the aircraft launches
