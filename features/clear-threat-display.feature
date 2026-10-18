Feature: Clear threat weather displays
  As a mission planner
  I want the map to show a clear color field for threat weather
  and a focused route-exposure view
  so that overlapping interfaces do not make the overview unusable.

  Background:
    Given a Gulf War demo world with threats, tasks, and planned routes
    And the cost-grid overlay is available

  Scenario: Solid weather-radar cost field is continuous and readable
    When the cost grid is toggled on
    Then the map shows a continuous regional field made of solid, opaque, non-overlapping cells
    And neighbouring covered cells abut edge-to-edge and connect into regional zones instead of floating as isolated shapes
    And the selected cell size and hex-versus-square controls still govern the field layout
    And the field is sampled densely enough at demo scale for neighbouring cells to connect visually
    And cells use a clear intensity ramp from green (low) through yellow and orange to red (critical)
    And no alpha stacking or cell strokes fight the fills
    And threat centers remain points
    And routes and task markers remain crisp on top of the field

  Scenario: Rendering order and layer toggles are independent
    Given the solid cost field is visible
    Then the displayed layers follow the order cost field, then rings, then routes, then markers, then labels
    When the vector rings toggle is off
    Then jam and lethal circles are not drawn
    When the vector rings toggle is on
    Then thin solid or dashed rings appear around threat centers
    And the cost field, rings, threat points, routes, and tasks can be toggled independently

  Scenario: Display field matches the cost-grid supplier
    Given the cost-grid supplier is active
    When a plan is generated
    Then the displayed cost field uses the same threat radii, severity weights, max aggregation, and intensity values as the supplier
    And routes avoid or penalize high-cost cells consistently with the display

  Scenario: Route-exposure focus marks only impacted points and sub-segments
    Given a selected aircraft route in the details view
    When the route-exposure mode is active
    Then the base route remains visible without a whole-leg exposure wash
    And only the route points and short sub-segments inside threat coverage are marked jammed or lethal
    And clear portions of a leg remain clear even when another portion of the same leg is impacted
    And threat rings appear only for a selected or hovered threat, and only that threat's rings are drawn cleanly
    And a small inset shows the overall theater field
    And the side panel lists threats that affect the route with exposure and severity

  Scenario: Band means frequency band, not exposure, task, or platform type
    Given a threat that affects the selected route
    When route exposure is shown in the map, legend, tooltip, or side panel
    Then exposure is described only as clear, jammed, or lethal
    And the threat's frequency band is shown separately when relevant
    And the word band is not used to mean Strike, ISR, or an aircraft type

  Scenario: Legend makes the encoding explicit
    When either display mode is shown
    Then a persistent legend explains the intensity ramp and the clear, jammed, and lethal exposure states
    And the legend states that frequency band is a threat or jammer RF band shown separately from exposure
    And aggregation rule (max overlapping contribution) is noted
