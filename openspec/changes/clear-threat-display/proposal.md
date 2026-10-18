# Proposal: Clear threat weather displays (Option 1 solid field + Option 4 route-exposure)

## Why

The current Plan tab cost-grid + threat circles produce an unusable overlapping semi-transparent mess instead of a clear regional color field based on threat weather. Operators cannot read intensity or exposure at a glance.

Related: #15, `docs/THREAT-COST-GRID-OPTIONS.md`.

## What

Add two complementary display modes:

1. **Option 1 — Solid weather-radar cost field**
   - Continuous, denser regional field of solid opaque, edge-to-edge, non-overlapping cells (hex or square) with a clear green → yellow → orange → red intensity ramp.
   - No alpha stacking, no cell strokes that fight the fill.
   - Existing nominal cell-size and hex-versus-square controls are preserved; rendering samples at half pitch so neighbouring cells connect into zones.
   - Threat centers as points; vector rings as a separate toggle.
   - Routes and tasks remain crisp on top.

2. **Option 4 — Route-exposure focus** (details drawer / selected route)
   - Keep the base route crisp; mark only the exact route points and short sub-segments actually inside threat coverage as jammed or lethal (never a whole-leg wash).
   - Threat rings appear only on selection or hover, and only for that threat.
   - Small inset theater overview with the same solid color field.
   - Side panel lists threats affecting the route with exposure, severity, and RF frequency band.

Terminology correction: **band** means only a threat/jammer RF frequency band. Route impact is described as exposure (clear / jammed / lethal), never as a task type (Strike/ISR) or platform type.

## Non-goals

- Changing route geometry or the cost-grid supplier pathing logic.
- Full 3-D voxels or multi-altitude search (altitude readiness is a display contract only for now).
- Replacing the existing cost-grid toggle; these modes refine what appears when it is on.

## Success criteria

- With the cost grid on, the map shows a readable, continuous solid field instead of disconnected shapes or a muddy overlap.
- Selecting a route in the details view shows the exact impacted points/sub-segments without cluttering the overview or washing whole legs.
- Legend, z-order, layer toggles, and RF-frequency-band terminology make the encoding explicit.
- OpenSpec + Gherkin + Beads track the work.
