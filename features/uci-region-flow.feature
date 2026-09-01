Feature: Region samples to UCI MissionPlan with operator feedback

  Scenario: Gulf region sample yields only IADS-class threats
    Given the bundled gulf threat fixture derived from fuzzy-reconciler
    When the planner loads threats
    Then every threat has a fixed-threat category
    And no airport records are planned against

  Scenario: Ingest plus plan emits MissionPlan XML
    Given a live planning session
    When the operator ingests the gulf region sample and runs a plan cycle
    Then GET /api/uci/export returns MissionPlan and RoutePlan XML

  Scenario: Off-corridor platform produces PLAN_DEVIATION
    Given a planned GO route
    When a live position is several nm off the RoutePlan
    Then MissionPlanExecutionStatus is OFF_PLAN or WATCH
    And the attention item includes kind, icon, and title

  Scenario: In-mission insert returns TaskCommand acknowledgement
    Given a planned aircraft
    When the operator inserts a strike via POST /api/tasks/insert
    Then the response includes UCI TaskCommand XML
    And feedback kind is RETASK

  Scenario: EOB identity keys pass through to OrderOfBattle
    Given a region fixture with eob_record_id and elnot attributes
    When the planner ingests threats and exports UCI
    Then OrderOfBattle records include those identity keys
    And Task TargetEntityID equals the fuzzy entity id

  Scenario: OOB update requests validation without mutating RoutePlan
    Given an exported MissionPlan that references threat entity ids
    When a new OrderOfBattle version changes one of those entities
    Then MissionPlanValidationCommand reason is ORDER_OF_BATTLE
    And RoutePlan waypoint coordinates are unchanged until a new MissionPlan version

  Scenario: Strike tasks seed DMPI and Prioritization
    Given a plan cycle with at least one STRIKE task
    When UCI is exported
    Then a DMPI record exists for the strike target entity
    And Prioritization ranks include that entity
