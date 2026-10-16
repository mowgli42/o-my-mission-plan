# Mockups: Clear threat weather displays

These notes accompany the OpenSpec change `openspec/changes/clear-threat-display/` and the Gherkin feature `features/clear-threat-display.feature`.

## Option 1 — Solid weather-radar cost field

Non-overlapping solid cells with a clear green → yellow → orange → red ramp. No alpha stacking or fighting strokes. Threat centers as points; vector rings are a separate toggle. Routes and tasks stay crisp on top.

Use this as the default when the cost-grid toggle is on (Plan tab).

## Option 4 — Route-exposure focus

Selected route segments colored by exposure band (clear / jam / lethal). Threat rings only on selection or hover. Small inset theater overview. Side panel lists threats on the route with severity badges.

Use this in the details drawer / selected-route view.

## Additional directions (to be implemented)

1. **Rendering contract** — solid fills only, no cell strokes, strict z-order (field → rings → routes → markers → labels).
2. **Aggregation rule** — document and display max (current) vs sum in the legend.
3. **Cell size and style** — coarser regional zones and finer solid grid; hex vs square toggle.
4. **Layer toggles** — independent controls for cost field, vector rings, threat points, routes, tasks.
5. **Altitude readiness** — simple altitude selector even on the single 2-D layer so the same builder can later feed stacked layers.
6. **Legend and interaction** — persistent ramp + band meanings; click legend entry to filter/highlight.
7. **Consistency** — displayed field must match the cost-grid supplier field.

## Related

- Existing issue #15 (cost-grid toggle)
- `docs/THREAT-COST-GRID-OPTIONS.md`
- Current problematic screenshots in `docs/screenshots/`

Mockup images (solid field and route-exposure) should be committed alongside this README when available.
