# Tasks: Clear threat weather displays

## Phase 0 — Spec and tracking
- [ ] OpenSpec change validated (`npx @fission-ai/openspec validate clear-threat-display --strict` when CLI available)
- [ ] Gherkin feature `features/clear-threat-display.feature` mirrors the scenarios
- [ ] Beads epic + phase children linked to this change (or tracked via GH issues until `bd` works)
- [ ] Mockups committed under `docs/mockups/`

## Phase 1 — Rendering contract
- [ ] Update `app.js` cost-grid polygon rendering: solid fills, no strokes, fixed z-order
- [ ] Document aggregation (max) and color ramp in legend
- [ ] Separate toggles for field vs rings

## Phase 2 — Option 1 solid field
- [ ] Solid weather-radar style cells on Plan tab when cost grid is on
- [ ] Readable green → yellow → orange → red ramp
- [ ] Routes and tasks remain crisp

## Phase 3 — Option 4 route-exposure
- [ ] Details drawer colors selected route segments by exposure band
- [ ] Rings only on selection/hover
- [ ] Inset theater overview + enhanced threats-on-route panel

## Phase 4 — Additional directions
- [ ] Cell size / hex-vs-square control
- [ ] Simple altitude selector (display only)
- [ ] Legend interaction (click to highlight)
- [ ] Verify display field matches cost-grid supplier field

## Verification
- [ ] Manual check against current screenshots: no muddy overlap
- [ ] Gherkin scenarios pass (or are marked pending until UI automation exists)
- [ ] Performance remains acceptable with demo threat set
