# Design: Clear threat weather displays

## Rendering contract

- Solid, fully opaque fills only for the cost field. No alpha stacking. No cell strokes.
- Strict z-order above the base map: cost field → optional vector rings → routes → markers → labels.
- Aggregation (max vs sum) is documented and visible in the legend.
- Hover tooltips preferred over always-on labels.
- Layer toggles are independent: cost field, vector rings, threat points, routes, and tasks.
- Demo map zoom remains capped (`maxZoom` 12 on the shared dark base; details fit caps lower).

## Option 1 — Solid weather-radar field (IMG_8916 direction)

- Cells come from `build_hex_costgrid` (hex or square), driven by the existing cell-size and hex-versus-square controls.
- The selected `cell_nmi` remains the operator-facing nominal size. The renderer samples the same threat formula on a half-pitch lattice (`render_cell_nmi = cell_nmi / 2`) so neighbouring covered cells form a denser, more continuous regional field at demo scale.
- Cell polygons are exact edge-to-edge tilings: squares use exact half-spacings and pointy-top hexagons use the matching hex centre spacing. There are no intentional gaps and no overlaps.
- Colour is an intensity ramp derived from the supplier intensity value: LOW green, MEDIUM yellow, HIGH orange, CRITICAL red. It is not merely the contributing threat's severity label repeated across its whole disc.
- Threat centres stay as points. Jam and lethal rings remain a separate toggle.
- Routes and task markers are drawn after the field and remain crisp on top.
- The displayed intensity uses the same jam-radius falloff, severity weights, and max aggregation as the cost-grid supplier. The supplier and display must not silently diverge.

## Option 4 — Route-exposure focus (IMG_8915 direction)

- Used in the details drawer / selected-route view. It reuses `leg_exposure` / `build_exposure_report` and the routes-overview impact builder.
- The base selected route remains a crisp neutral line. Entire legs are **not** washed with one exposure colour.
- Each leg is sampled at roughly 2 nmi intervals. Consecutive impacted intervals are merged into short `exposure_spans` with route endpoints (`from`/`to`, fractions, lat/lon), and explicit `impacted_points` mark route vertices and span boundaries inside coverage.
- When no threat is selected, aggregate impacted sub-segments for affecting threats may be shown. When a threat is selected or hovered, only that threat's rings are drawn cleanly and its per-threat spans are used for the exposure marks.
- A small inset theater overview shows the same solid field (opaque, simplified by scale), and the side panel lists threats affecting the route with exposure, severity, closest approach, impacted sub-segment count, and frequency band.

## Terminology: frequency band vs exposure

- **Frequency band** (`frequency_band`) means only the RF frequency band used by a threat or jammer (for example S-band or X-band). Region/EOB input may arrive as an attribute named `band`; it is stored and displayed as a frequency band.
- **Exposure** describes what happens to a route point or sub-segment: `CLEAR`, `JAMMED`, or `LETHAL`, based on that threat's jam/lethal radii.
- Do not use “band” to mean Strike, ISR, an aircraft/platform type, or a route-impact category. UI labels, tooltips, legends, API fields, and Gherkin use exposure language for route impact and show `frequency_band` separately when relevant.

## Additional directions (must address)

1. **Rendering contract** — solid opaque fills, no fighting strokes, documented z-order.
2. **Aggregation rule** — max overlapping contribution; shown in the legend.
3. **Cell size and style** — existing nominal cell-size control and hex-vs-square toggle preserved; half-pitch sampling is a rendering densification, not a new operator control.
4. **Layer toggles** — cost field, vector rings, threat points, routes, tasks independently.
5. **Altitude readiness** — even on the single 2-D layer, expose a simple altitude selector so the same field builder can later feed stacked layers.
6. **Legend and interaction** — persistent intensity ramp + clear/jammed/lethal exposure states; clicking an intensity level highlights it. Frequency band is explained as RF-only.
7. **Export / search consistency** — display field must stay identical in formula to the field used by the cost-grid supplier.

## Risks

- Half-pitch sampling increases cell count by roughly four times for the same nominal control. Acceptable for the demo threat set; monitor as in #15.
- Sub-segment sampling is an approximation of continuous circle/segment intersection. The roughly 2 nmi sample step is the stated demo-scale precision; span endpoints are sample boundaries, not analytic circle intersections.
- Altitude selector is display-only until stacked layers are implemented.

## Alternatives considered

- Smooth heatmap + crisp rings (Option 2) and coarse regional zones + altitude slices (Option 3) were sketched but deferred. Option 1 + Option 4 cover the immediate usability gap.
