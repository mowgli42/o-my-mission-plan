# Tasks: Clear threat weather displays

## Phase 0 — Spec and tracking
- [x] OpenSpec change validated (`npx @fission-ai/openspec validate clear-threat-display --strict` when CLI available)
- [x] Gherkin feature `features/clear-threat-display.feature` mirrors the scenarios
- [x] Beads epic + phase children linked to this change (`omp-d2t` / GH #33–#36)
- [x] Mockups committed under `docs/mockups/` (notes; images optional follow-up)

## Phase 1 — Rendering contract
- [x] Update `app.js` cost-grid polygon rendering: solid fills, no strokes, fixed z-order
- [x] Document aggregation (max) and color ramp in legend
- [x] Separate toggles for field vs rings

## Phase 2 — Option 1 solid field
- [x] Solid weather-radar style cells on Plan tab when cost grid is on
- [x] Readable green → yellow → orange → red ramp
- [x] Routes and tasks remain crisp

## Phase 3 — Option 4 route-exposure
- [x] Details drawer colors selected route segments by exposure band
- [x] Rings only on selection/hover
- [x] Inset theater overview + enhanced threats-on-route panel

## Phase 4 — Additional directions
- [x] Cell size / hex-vs-square control
- [x] Simple altitude selector (display only)
- [x] Legend interaction (click to highlight)
- [x] Verify display field matches cost-grid supplier field (same `build_hex_costgrid` API)

## Verification
- [ ] Manual check against current screenshots: no muddy overlap
- [x] Gherkin scenarios tracked (UI automation pending; API/UI control tests cover contract)
- [ ] Performance remains acceptable with demo threat set
