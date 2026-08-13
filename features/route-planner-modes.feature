Feature: Route planner modes and COA-aligned timed allocation
  As a mission planner
  I want multiple route planner modes and capacity/time-aware allocation
  So that different COAs use different platform counts and geometries on the same task pool

  Background:
    Given a Gulf theater demo world with published waypoints and threats
    And platforms with capacity limits and constant-burn fuel models
    And tasks that may include time windows and target groupings

  # --- Validated (prototype must exercise) ---

  @validated
  Scenario: Efficient allocation prefers fewer platforms when capacity allows
    Given a set of tasks that fit on fewer airframes by capacity
    When I allocate with coa_bias efficient and minimize_platform_count true
    Then platforms_used is less than or equal to allocation with coa_bias spread_field
    And unallocated and capacity_snapshot are returned

  @validated
  Scenario: Threat avoid path differs from efficient when a high threat blocks the direct radial
    Given an aircraft assigned tasks whose short path crosses a HIGH or CRITICAL threat jam radius
    When I plan with mode threat_avoid
    And I plan with mode efficient
    Then the threat_avoid waypoint sequence is not identical to efficient
    And threat_avoid returns an exposure_score
    And both routes use only published waypoint kinds

  @validated
  Scenario: Area loiter provides dwell metric for ISR
    Given an ISR aircraft assigned a collection task
    When I plan with mode area_loiter
    Then the route includes a cyclic published-fix pattern or repeated hold fix
    And loiter_minutes is reported
    And fuel propagation accounts for loiter debit or documents the estimate

  @validated
  Scenario: Iterate stores a Mission Option for COA comparison
    When I POST iterate with a route_mode and allocation coa_bias
    Then an option_id is returned with plans for each assigned platform
    And summary includes platforms_used, go, nogo, unallocated, total_distance_nmi

  @validated
  Scenario: Time windows mark infeasible-by-time without silent assignment
    Given a task whose latest time is earlier than any platform ETA under nominal speed
    When I allocate with respect_time_windows true
    Then the task appears in infeasible_by_time_task_ids or unallocated with a time note

  # --- Future (aspirational — not claimed validated) ---

  @future
  Scenario: Spread field guarantees continuous-space separation
    When two fighters are planned with mode spread_field
    Then minimum lateral separation is enforced in continuous geometry (MAPF)

  @future
  Scenario: Optimal time-window mTSP allocation
    When tasks have tight overlapping windows
    Then allocation is optimal under a declared MILP or mTSP solver

  @future
  Scenario: RRT star kinodynamic threat penetration
    When planning in dense 3-D threat terrain
    Then the planner returns a dynamically feasible spline not restricted to the published-fix graph
