# Design: Shared dark map base

## Base map

- Leaflet 1.9.4 from unpkg, pinned with SRI hashes (this repo has no bundler).
- Tiles: Esri World Dark Gray Canvas base + reference labels, `maxZoom` 12 on
  both the map and the tile layers, `opacity` 0.65 / 0.45 over the `#0b1220`
  console background. Attribution `© Esri, HERE, Garmin, © OpenStreetMap contributors`.
- CartoDB Dark Matter was the original target but watermarks un-keyed tiles
  since Sept 2026; a key-free provider keeps the suite demo-simple.

## Overlays stay string-built SVG

- `PlanOverlayRenderer = L.SVG.extend(...)` adds one `<g class="plan-overlay">`
  to Leaflet's own SVG renderer container. `renderMap()` keeps building the
  same SVG strings and writes them into that group.
- `project(lat, lon)` becomes `map.latLngToLayerPoint`, so overlay geometry is
  in the same layer-point space as the renderer's viewBox. Marker and text
  sizes stay in screen pixels at every zoom.
- The renderer's `update` event (fired after pan / zoom / resize) re-renders
  the last options for that map; Leaflet's zoom animation scales the SVG
  until the re-render lands.
- Threat groups opt back into pointer events (`.plan-overlay .threat-g`);
  everything else is click-through so map dragging works.

## Fit and resize

- Each map keeps a `home` bounds (theater for Plan / inset, route bounds for the
  details map) and auto-fits it on container resizes until the user pans or
  zooms. The Plan frame shrinks once the exposure panel renders, which is why a
  one-shot `fitBounds` was not enough. **Theater** restores auto-fit.
- Drawer maps are created lazily on first open (visible container → correct size).

## Risks

- `L.SVG._initContainer` / `_container` are Leaflet internals; the version is
  pinned and the dependency is isolated in one small subclass.
- No-network demos: Leaflet missing → plain SVG fallback with the legacy fixed
  projection (overlays only, no tiles).
