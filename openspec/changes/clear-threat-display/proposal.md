# Proposal: Clear threat weather displays (Option 1 solid field + Option 4 route-exposure)

## Why

The current Plan tab cost-grid + threat circles produce an unusable overlapping semi-transparent mess instead of a clear regional color field based on threat weather. Operators cannot read intensity or exposure at a glance.

Related: #15, `docs/THREAT-COST-GRID-OPTIONS.md`.

## What

Add two complementary display modes:

1. **Option 1 — Solid weather-radar cost field**
   - Non-overlapping solid cells (hex or square) with a clear green → yellow → orange → red intensity ramp.
   - No alpha stacking, no cell strokes that fight the fill.
   - Threat centers as points; vector rings as a separate toggle.
   - Routes and tasks remain crisp on top.

2. **Option 4 — Route-exposure focus** (details drawer / selected route)
   - Color only the selected route segments by exposure band (clear / jam / lethal).
   - Threat rings appear only on selection or hover.
   - Small inset theater overview with simple color field.
   - Side panel lists threats on the route with severity badges.

## Non-goals

- Changing route geometry or the cost-grid supplier pathing logic.
- Full 3-D voxels or multi-altitude search (altitude readiness is a display contract only for now).
- Replacing the existing cost-grid toggle; these modes refine what appears when it is on.

## Success criteria

- With the cost grid on, the map shows a readable solid field instead of a muddy overlap.
- Selecting a route in the details view shows exposure-colored segments without cluttering the overview.
- Legend, z-order, and layer toggles make the encoding explicit.
- OpenSpec + Gherkin + Beads track the work.
