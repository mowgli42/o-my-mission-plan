Feature: Shared dark map base
  As a mission planner
  I want the Plan map to sit on the same key-free dark base map as debrief and battlespace
  so that the o-my consoles look alike and I can read overlays against real geography.

  Background:
    Given a Gulf War demo world with threats, tasks, and planned routes

  Scenario: Dark tiles under the Plan overlays
    When the Plan tab map renders
    Then dark base tiles are visible beneath the cost field, routes, threats and markers
    And the attribution control names the tile provider
    And the view fits the PSAB to Kuwait / Iraq theater

  Scenario: Demo-scale zoom cap
    When the user zooms in repeatedly
    Then the map stops at zoom 12
    And the zoom-in control is disabled

  Scenario: Overlays follow pan and zoom
    Given the cost field and vector rings are toggled on
    When the user pans or zooms the map
    Then cells, rings, routes and markers are re-projected and stay aligned with the tiles

  Scenario: No API key
    Then no map provider key is present in the repository or required at runtime
