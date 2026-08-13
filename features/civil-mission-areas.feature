Feature: Civil and mission routing regimes
  As a mission planner
  I want civil waypoint routes to connect at handoffs to mission cost-grid routes
  So that transit is structured and the fight area has threat-aware autonomy

  Background:
    Given a demo world with a defined MissionArea containing threats and tasks
    And entry and exit handoff fixes on the area boundary
    And civil navaids outside the area toward the home airbase

  @validated
  Scenario: Composite route has civil ingress, mission segment, civil egress
    When I plan a composite route for an aircraft with tasks inside the MissionArea
    Then the route begins with a civil segment from home to an entry handoff
    And a mission segment runs from that entry handoff to an exit handoff
    And a civil segment returns from the exit handoff to home
    And the entry handoff id is shared between civil ingress end and mission start
    And the exit handoff id is shared between mission end and civil egress start

  @validated
  Scenario: Mission segment is threat-cost driven; civil is not
    Given a HIGH threat inside the MissionArea on the short path between entry and a task
    When I plan composite with mission mode threat_avoid
    Then the mission segment waypoint sequence reflects threat cost avoidance
    And the civil ingress segment does not detour through the mission cost grid

  @validated
  Scenario: Export remains published and mission fix kinds only
    When a composite route is produced
    Then every waypoint kind is airbase, navaid, or mission
    And no anonymous grid-cell ids appear on the exported route

  @future
  Scenario: Multiple mission areas with civil connectors between them
    Given two MissionAreas along a campaign axis
    When planning a multi-area package
    Then civil connector segments link exit of the first area to entry of the second
