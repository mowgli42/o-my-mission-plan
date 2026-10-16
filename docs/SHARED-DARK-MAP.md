# Shared dark map base (o-my suite convention)

The Plan tab map and the route-details maps draw their overlays on the same
key-free dark base map as `o-my-debrief` and `battlespace-manager`, so the
plan / battlespace / debrief consoles look alike in demos. The canonical
write-up lives in the reference repo:
[`o-my-debrief/docs/SHARED-DARK-MAP.md`](https://github.com/mowgli42/o-my-debrief/blob/main/docs/SHARED-DARK-MAP.md).

## The convention

| Setting | Value |
| --- | --- |
| Library | Leaflet 1.9.4 (pinned from unpkg with SRI; no bundler in this repo) |
| Tiles | Esri World Dark Gray Canvas — base + reference (labels) layers |
| Base URL | `https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}` |
| Labels URL | `https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}` |
| `maxZoom` | **12** — regional demo scale, no street-level detail |
| Opacity | base 0.65, labels 0.45 over a `#0b1220` container background |
| Attribution | `© Esri, HERE, Garmin, © OpenStreetMap contributors` |
| API key | none; no paid provider |

Why not CartoDB Dark Matter (the original plan)? CARTO watermarks every
un-keyed tile with "API KEY REQUIRED" since September 2026, so the only way to
keep it would be to commit or inject a key. The suite stays key-free instead;
if a keyed provider is ever adopted, change the reference constant in
`o-my-debrief` first and the copies here and in `battlespace-manager` after.

## Where it lives in this repo

Everything is in `src/omy_mission_plan/static/`:

- `index.html` loads Leaflet CSS/JS (pinned 1.9.4, SRI hashes) and hosts three
  map containers: `#map` (Plan tab), `#detail-map` and `#detail-inset`
  (route-details drawer).
- `app.js` — `SUITE_DARK_TILES` / `SUITE_DARK_LABELS` constants, `createBaseMap()`,
  and `PlanOverlayRenderer`, an `L.SVG` renderer subclass with one extra `<g>`
  that the existing string-built overlays (solid cost field, vector rings,
  navaids, routes, task / threat markers, aircraft scrub) are written into.
  Leaflet keeps that SVG aligned in layer-point space across pan and zoom and
  re-fires `update`, which re-projects the overlays via `map.latLngToLayerPoint`.
  Overlay geometry, toggles, legend, and the cost-grid supplier are unchanged.
- `styles.css` — dark theme for Leaflet controls / attribution, overlay text
  halo, and pointer-events opt-in for threat markers.

Behaviour notes:

- The Plan map auto-fits the PSAB → Kuwait / Iraq theater and keeps doing so
  through container resizes until the user pans or zooms; **Theater** in the
  map toolbar restores it.
- The details map fits the selected route (cap zoom 9); the inset is a
  non-interactive theater overview.
- If the Leaflet CDN is unreachable the overlays fall back to a plain SVG with
  the legacy fixed theater projection, so the console still works offline
  (without tiles).
