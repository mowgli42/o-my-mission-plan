# Tasks: Shared dark map base

## Phase 0 — Spec and tracking
- [x] OpenSpec change (`shared-dark-map-base`) + Gherkin mirror `features/shared-dark-map-base.feature`
- [x] GitHub epic #39 linked to siblings (o-my-debrief#22, battlespace-manager#38)

## Phase 1 — Base map
- [x] Load pinned Leaflet 1.9.4 (SRI) in `index.html`; swap SVG containers for map hosts
- [x] `SUITE_DARK_TILES` / `SUITE_DARK_LABELS` constants matching the suite convention; `maxZoom` 12 on map + layers
- [x] Dark theme for Leaflet controls / attribution

## Phase 2 — Overlays on top
- [x] `PlanOverlayRenderer` (L.SVG subclass) hosting the string-built overlays
- [x] `project()` via `latLngToLayerPoint`; re-render on renderer `update`
- [x] Threat markers remain clickable / hoverable; legend + toggles unchanged
- [x] Details drawer map (route fit) + non-interactive inset (theater fit)

## Phase 3 — Fit / resize / docs
- [x] Auto-fit home bounds through container resizes until user interaction; **Theater** button
- [x] `docs/SHARED-DARK-MAP.md` + README pointers
- [x] Offline fallback (plain SVG) when Leaflet is unavailable

## Verification
- [x] Headless Chromium run: tiles 200, overlays present after toggles / zoom / pan, zoom-in disabled at cap, drawer maps render
- [x] `make test` (API) still green
- [ ] `make screenshots` refresh of `docs/screenshots/` (follow-up, needs a display host)
