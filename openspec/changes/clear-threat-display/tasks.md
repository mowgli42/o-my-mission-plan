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
- [x] Details drawer marks selected-route exposure at point/sub-segment level
- [x] Rings only on selection/hover
- [x] Inset theater overview + enhanced threats-on-route panel

## Phase 4 — Additional directions
- [x] Cell size / hex-vs-square control
- [x] Simple altitude selector (display only)
- [x] Legend interaction (click to highlight)
- [x] Verify display field matches cost-grid supplier field (same `build_hex_costgrid` API)

## Phase 5 — Corrections (IMG_8916 / IMG_8915 + screenshot review)
- [x] Option 1: exact edge-to-edge tiling + half-pitch sampling so the solid field reads as continuous regional zones; intensity-derived ramp; opaque fills
- [x] Option 4: replace whole-leg colouring with `exposure_spans` and `impacted_points` (roughly 2 nmi sampling); selected/hovered threat draws only its rings and spans
- [x] Terminology: `frequency_band` is RF-only; route impact API/UI fields use exposure (clear / jammed / lethal), not Strike/ISR/platform “bands”
- [x] Gherkin + design notes updated for continuous field, point-level exposure, and band terminology

## Phase 6 — Details Impact timeline correction
- [x] Impact rail uses `weather_impact` (cost-field intensity ramp), not per-threat clear/jammed/lethal teal wash
- [x] Onboard / Offboard jam-support rails list jammer packages with RF frequency band
- [x] Gherkin + design notes + screenshot 05 updated

## Phase 7 — Threat data bounds + RF band filter
- [x] Cost-field bounds expand from each threat jam disc (no Iraq clip at lat 34)
- [x] Region ingest / fixture fills missing frequency bands (ELNOT / category defaults)
- [x] All-up vs per-band weather selector; threat points filtered with the field
- [x] Gherkin + design notes updated

## Verification
- [x] Manual check against current screenshots: no muddy overlap, no disconnected hex field, no whole-leg wash
- [x] Details Impact rail shows green→yellow→orange→red matching Plan weather under the route
- [x] Gherkin scenarios tracked (UI automation pending; API/UI control tests cover contract)
- [x] Performance remains acceptable with demo threat set (~205 rendered cost cells at default settings; 67 tests pass)
