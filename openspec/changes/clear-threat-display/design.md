# Design: Clear threat weather displays

## Rendering contract

- Solid fills only for the cost field. Fixed or no alpha. No cell strokes.
- Strict z-order: cost field → optional vector rings → routes → markers → labels.
- Aggregation (max vs sum) is documented and visible in the legend.
- Hover tooltips preferred over always-on labels.

## Option 1 — Solid weather-radar field

- Cells from existing `build_hex_costgrid` (or square equivalent).
- Color ramp: LOW green, MEDIUM yellow, HIGH orange, CRITICAL red (solid).
- Separate toggle for jam/lethal vector rings.
- Cell size and style (hex vs square) configurable for prototype.

## Option 4 — Route-exposure focus

- Reuses existing `leg_exposure` / `build_exposure_report`.
- Selected route segments colored by band (clear / jam / lethal).
- Rings only when a threat is selected or hovered.
- Inset overview shows the solid field at reduced opacity or simplified.
- Side panel already present in the details drawer; enhance with clear badges.

## Additional directions (must address)

1. **Rendering contract** — solid fills, no fighting strokes, documented z-order.
2. **Aggregation rule** — confirm max (current) or switch to sum; show in legend.
3. **Cell size and style** — prototype coarser regional zones and finer solid grid; hex vs square toggle.
4. **Layer toggles** — cost field, vector rings, threat points, routes, tasks independently.
5. **Altitude readiness** — even on the single 2-D layer, expose a simple altitude selector so the same field builder can later feed stacked layers.
6. **Legend and interaction** — persistent color ramp + band meanings; clicking a legend entry filters or highlights.
7. **Export / search consistency** — display field must stay identical to the field used by the cost-grid supplier.

## Risks

- Changing cell rendering may affect performance on denser threat sets (monitor as in #15).
- Altitude selector is display-only until Option B layers are implemented.

## Alternatives considered

- Smooth heatmap + crisp rings (Option 2) and coarse regional zones + altitude slices (Option 3) were sketched but deferred. Option 1 + Option 4 cover the immediate usability gap.
