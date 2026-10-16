# Proposal: Shared dark map base (Leaflet + key-free dark tiles)

## Why

The Plan tab map was a custom 640x520 SVG with an equirectangular projection and
no geographic base. Debrief and battlespace-manager already draw on a Leaflet
dark tile map, so the three consoles did not look alike and overlay helpers
could not be shared. GitHub #39 (epic); siblings mowgli42/o-my-debrief#22 and
mowgli42/battlespace-manager#38.

## What

- Layer the existing overlays on a Leaflet map with the suite's shared,
  key-free dark base tiles (regional scale, zoom capped at 12).
- Keep every existing overlay (solid cost field, vector rings, navaids / fixes,
  routes, task and threat markers, aircraft scrub), every layer toggle, and the
  legend exactly as they are; only the projection underneath changes.
- Apply the same base to the route-details map and its inset.
- Document the convention (`docs/SHARED-DARK-MAP.md`) so the sibling repos stay
  in sync.

## Non-goals

- Street-level or high-zoom tiles; paid Mapbox / Google keys; any committed API key.
- Changing the cost-grid supplier, route geometry, or exposure logic.
- Rewriting the overlays as native Leaflet vector layers (string-built SVG stays).

## Success criteria

- Plan view shows dark tiles under the overlays; no API key anywhere in the repo.
- Zoom cannot exceed 12; the view fits the PSAB → Kuwait / Iraq theater by default.
- Cost field, rings, threats, routes and aircraft toggles behave as before.
- Visual style matches debrief / battlespace (same tiles, same cap, dark controls).
