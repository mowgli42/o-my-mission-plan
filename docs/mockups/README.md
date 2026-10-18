# Mockups: Clear threat weather displays

These notes accompany the OpenSpec change `openspec/changes/clear-threat-display/` and the Gherkin feature `features/clear-threat-display.feature`.

## Option 1 — Solid weather-radar cost field (IMG_8916 direction)

Continuous regional field of non-overlapping, solid, opaque cells with a clear green → yellow → orange → red intensity ramp. No alpha stacking or fighting cell strokes. Neighbouring covered cells abut edge-to-edge and connect into zones rather than floating as isolated hexagons/squares. The existing nominal cell-size and hex-versus-square controls are preserved; rendering samples the supplier formula at half pitch for demo-scale continuity. Threat centers stay as points; jam/lethal vector rings are a separate toggle. Routes and tasks stay crisp on top.

Use this as the default when the cost-grid toggle is on (Plan tab).

## Option 4 — Route-exposure focus (IMG_8915 direction)

In the details drawer / selected-route view, do not wash entire route legs. Keep the base route crisp and mark only the exact route points and short sub-segments that fall inside a threat's jam or lethal coverage. When a threat is selected or hovered, draw only that threat's rings cleanly and show its affected sub-segments. Keep a small inset theater overview and a side panel listing the threats affecting the route.

## Terminology

**Band** means frequency band only: the RF band used by a threat or jammer (shown per threat as `frequency_band` when relevant). It does not mean Strike, ISR, or an aircraft/platform type. Route impact is exposure language only: **clear**, **jammed**, or **lethal**.

## Additional directions

1. **Rendering contract** — solid opaque fills only, no cell strokes, strict z-order (field → rings → routes → markers → labels).
2. **Aggregation rule** — max overlapping contribution, shown in the legend.
3. **Cell size and style** — existing nominal cell-size control plus hex vs square toggle; denser half-pitch rendering for continuity.
4. **Layer toggles** — independent controls for cost field, vector rings, threat points, routes, tasks.
5. **Altitude readiness** — simple altitude selector even on the single 2-D layer so the same builder can later feed stacked layers.
6. **Legend and interaction** — persistent intensity ramp + clear/jammed/lethal exposure meanings; click an intensity level to filter/highlight. Frequency band is explained separately as RF-only.
7. **Consistency** — displayed field must match the cost-grid supplier formula (radii, severity weights, max aggregation).

## Related

- Existing issue #15 (cost-grid toggle)
- `docs/THREAT-COST-GRID-OPTIONS.md`
- Current screenshots in `docs/screenshots/`

Mockup images (IMG_8916 solid field and IMG_8915 route-exposure) should be committed alongside this README when available.
