# Delta: o-my-mission-plan — R15 Map layers

## MODIFIED Requirement: R15 — Map layers (cost grid, threats, exposure, scrub)

The Plan tab and route-details maps SHALL render their overlays on the o-my
suite shared dark base map: a Leaflet map with key-free dark raster tiles,
zoom capped at 12 (regional demo scale), with provider attribution visible.
No API key SHALL be required or committed. Existing overlays (toggleable cost
grid, threat radii, legs threats "see", scrubbable aircraft) and their toggles
SHALL be preserved on top of the base map.

#### Scenario: Dark tiles under the Plan overlays
- GIVEN the Plan tab is open with the demo world loaded
- WHEN the map renders
- THEN dark base tiles are visible beneath the cost field, routes, threats and markers
- AND the attribution control names the tile provider
- AND the view fits the PSAB → Kuwait / Iraq theater

#### Scenario: Demo-scale zoom cap
- GIVEN the Plan map
- WHEN the user zooms in repeatedly
- THEN the map stops at zoom 12 and the zoom-in control is disabled

#### Scenario: Overlays follow pan and zoom
- GIVEN the cost field and vector rings are toggled on
- WHEN the user pans or zooms the map
- THEN cells, rings, routes and markers are re-projected and stay aligned with the tiles
