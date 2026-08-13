# IxDF feedback — plan deviation and in-mission tasking

Operator-facing contract for battlespace-manager. Grounded in Nielsen/Molich 10 UI guidelines, IxDF color-in-UX, and IxDF UI design principles. Complements o-my `docs/UI_IMPROVEMENTS_IXDF.md`.

---

## Who / why / what / how

- **Who:** CAOC monitor on the COP (not a planner hunched over a form).
- **Why:** If a platform leaves the corridor, or an operator retasks mid-mission, the picture must say so immediately — otherwise the map lies.
- **What:** Planned route vs flown route, execution state, retask ACK/NACK, return-to-plan.
- **How:** Bus messages first (`MissionPlanExecutionStatus`, `TaskStatus`, `ThreatNotification`); UI only renders them. Color is never the only cue.

---

## Heuristics applied

| # | Guideline | In this flow |
|---|-----------|----------------|
| 1 | **Visibility of system status** | Header chip per package: On plan / Watch / Off plan. Attention rail item within ~1 tick of `MissionPlanExecutionStatus`. |
| 2 | **Match the real world** | “Off plan” means cross-track vs the RoutePlan the package briefed — not a mystery score. Callsigns, not service names. |
| 3 | **User control and freedom** | Retask is reversible: `TaskCancelCommand` + “Return to plan” republishes the last approved `RoutePlan`. |
| 4 | **Consistency** | Same Attention Rail, same phase colors, same task lifecycle vocabulary (`QUEUED`…`ABORTED`). New kinds: `PLAN_DEVIATION`, `RETASK`. |
| 5 | **Error prevention** | STRIKE retask while SEAD predecessor incomplete → confirm dialog (“SEAD not complete on {site}”). Disabled primary if ROE block. |
| 6 | **Recognition rather than recall** | Planned dashed route stays on the map while actual flies. Task row shows **planned task** vs **active task**. |
| 7 | **Flexibility** | Click platform → Retask. Keyboard: `R` retask selected, `Esc` cancel compose. |
| 8 | **Aesthetic / minimalist** | No deviation chrome until WATCH. Clutter stays off until the corridor is violated. |
| 9 | **Recognize, diagnose, recover** | Message: “VIPER01 is 6.2 nm east of IP→TGT. Return to plan or approve new RoutePlan.” Not “Error 500”. |
| 10 | **Help** | Tooltip on the chip: corridor thresholds 2 / 5 / 12 nm. Link to this doc. |

---

## Color as a functional language (not decoration)

Palette roles (pair **tone + icon + text**; do not rely on hue):

| Severity | Tone token | Icon | Text |
|----------|------------|------|------|
| NONE | `on-plan` | check | On plan |
| WATCH | `watch` | amber mark | Watch — drifting from planned route |
| OFF_PLAN | `off-plan` | break | Off plan — platform left the corridor |
| CRITICAL | `critical` | alert | Critical deviation — return-to-plan or replan |
| RETASK | `retask` | fork | In-mission retask — awaiting / accepted |

60/30/10: COP neutrals dominate; planned cyan and actual white are secondary; deviation/retask accents are the 10%.

WCAG: chip text vs background ≥ 4.5:1. Pattern (dashed vs solid) encodes planned vs actual independently of color.

---

## Surfaces

### Map (Battlespace tab)

- **Planned `RoutePlan`:** dashed, labeled waypoints (`INGRESS`, `IP`, `TGT-*`, `EGRESS`).
- **Actual:** solid breadcrumb from `PlatformStatus`.
- **Off-plan:** hatch or break mark at the closest RoutePlan leg + callsign label (“OFF PLAN 6.2 nm”).
- Clicking the platform selects it globally (existing IxDF consistency).

### Attention rail

New kinds (filter chips like TST/POP):

- `PLAN_DEVIATION` — from `MissionPlanExecutionStatus.deviation_severity` ∈ {WATCH, OFF_PLAN, CRITICAL}
- `RETASK` — `in_mission_retask=true` or `TaskCommand` in flight until `TaskStatus` ASSIGNED/rejected

`aria-live="polite"` on the summary line (already on the rail).

### Decisions / tasking panel

When operator tasks a live platform:

1. Compose `TaskCommand` (target, role, reason).
2. Optimistic row: **Sending…** (status visible).
3. On `TaskStatus`: **Accepted — {callsign} turning** or **Rejected — {reason}**.
4. Map shows magenta retask stub until the new `RoutePlan` (from `RouteModificationRequest`) lands, then that becomes the planned dashed line.

### Mission thread / timeline

Existing timeline tab: add `MISSION_PLAN_ACTIVATED`, `TASK_EXECUTE`, `OFF_PLAN`, `RETASK` as scenario-class events so plan and tasks share one axis (recognition over recall).

---

## Thresholds (shared with `feedback.py`)

| Cross-track | Severity | UI |
|-------------|----------|-----|
| < 2 nm | NONE | No extra chrome |
| 2–5 nm | WATCH | Chip + rail, no modal |
| 5–12 nm | OFF_PLAN | Rail + map break + optional confirm if they issue STRIKE |
| ≥ 12 nm | CRITICAL | Rail immediate; suggest replan |

---

## Control and recovery

| Operator action | Bus | Feedback |
|-----------------|-----|----------|
| Activate plan | `MissionPlanActivationCommand` | `MissionPlanActivationStatus` + chip EXECUTING |
| Retask platform | `TaskCommand` | `TaskStatus` + `RETASK` rail item |
| Cancel retask | `TaskCancelCommand` | `TaskCancelCommandStatus` + rail clears |
| Return to plan | `RouteModificationRequest` to last approved RoutePlan **or** re-`MissionPlanActivation` of original | New `RoutePlan` + ON_PLAN |

Never change sim truth only in the UI.
