Feature: Clear threat weather displays
  As a mission planner
  I want the map to show a clear color field for threat weather
  and a focused route-exposure view
  so that overlapping interfaces do not make the overview unusable.

  Background:
    Given a Gulf War demo world with threats, tasks, and planned routes
    And the cost-grid overlay is available

  Scenario: Solid weather-radar cost field is readable
    When the cost grid is toggled on
    Then the map shows non-overlapping solid cells
    And cells use a clear intensity ramp from green (low) through yellow and orange to red (critical)
    And no semi-transparent overlapping fills create a muddy mess
    And routes and task markers remain crisp on top of the field

  Scenario: Vector rings are independent of the solid field
    Given the solid cost field is visible
    When the vector rings toggle is off
    Then jam and lethal circles are not drawn
    When the vector rings toggle is on
    Then thin solid or dashed rings appear around threat centers

  Scenario: Route-exposure focus colors only the selected route
    Given a selected aircraft route in the details view
    When the route-exposure mode is active
    Then segments of that route are colored by exposure band (clear, jam, or lethal)
    And threat rings appear only for a selected or hovered threat
    And a small inset shows the overall theater field
    And the side panel lists threats that see the route with severity badges

  Scenario: Legend makes the encoding explicit
    When either display mode is shown
    Then a persistent legend explains the color ramp and band meanings
    And aggregation rule (max overlapping contribution) is noted

  Scenario: Display field matches the cost-grid supplier
    Given the cost-grid supplier is active
    When a plan is generated
    Then the displayed cost field uses the same intensity values as the supplier
    And routes avoid or penalize high-cost cells consistently with the display
