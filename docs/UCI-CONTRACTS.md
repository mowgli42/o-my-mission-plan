# Cross-stack UCI contracts (normative)

Bidirectional **send / ingest** field tables so a publisher and a consumer can implement independently. Catalog names are Open Arsenal **UCI 2.5** (`UCI_MessageDefinitions_v2_5_0.xsd`) and A-GRA **v5.0a** (`A-GRA_MessageDefinitions_v5_0_a.xsd`). Transport today: Redis `uci.*` (OMS ASB stand-in), Tier B UCI-Lite XML.

Hub repo: **o-my-mission-plan**. Sibling implementers copy these tables into their own specs; do not invent parallel field names.

Related: [UCI-MESSAGE-INTERACTIONS.md](UCI-MESSAGE-INTERACTIONS.md) · [UCI-GAPS.md](UCI-GAPS.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [IXDF-FEEDBACK.md](IXDF-FEEDBACK.md)

---

## How to read a hop

Every hop lists:

| Column | Meaning |
|--------|---------|
| **Publisher** | System of record for the message |
| **Consumer** | Must ingest listed required fields; MAY ignore optionals |
| **Topic** | Redis channel (constant name in `topics.py`) |
| **MessageType** | `uci:Header/uci:MessageType` = UCI 2.5 / A-GRA element name |
| **CorrelationID** | Join key. Mission thread = `MissionPlanID`. EOB thread = `OrderOfBattleID` |
| **Must persist** | Consumer stores this to act later (not fire-and-forget) |
| **Ignore OK** | Safe to drop without breaking the hop |

Envelope (all XML messages):

| Field | Required | Notes |
|-------|----------|-------|
| `uci:MessageID` | yes | Unique per publication |
| `uci:Timestamp` | yes | UTC `YYYY-MM-DDTHH:MM:SSZ` |
| `uci:Sender` | yes | Service id (`omy-mission-plan`, `scenario-director`, …) |
| `uci:MessageType` | yes | Catalog element name |
| `uci:CorrelationID` | yes on mission/EOB threads | See hop |

Namespaces: header `urn:uci:standard:1.0`; mission body `urn:omy:mission:1.0`; EOB body `urn:omy:eob:1.0` until Tier C XSD.

---

## Implementation order

Work hops **0 → 6**. Do not fly a MissionPlan (hop 3) until hop 0 topic constants exist in o-my and o-my-sim. Do not retask from the COP (hop 5) until hop 3 ACKs `TaskCommand`.

| # | Hop | Publisher → consumer | Beads / GH |
|---|-----|----------------------|------------|
| 0 | Shared topic + envelope constants | all repos | contracts first |
| 1 | EOB working set | fuzzy-reconciler → planner + sim | FR #16 + export issue |
| 2 | Deliberate plan export | o-my-mission-plan → sim + o-my | this repo |
| 3 | Activate + fly | o-my-sim → o-my + COP | sim ingest issues |
| 4 | Process + F2T2EA | o-my → COP + planner validation | o-my plan-monitor |
| 5 | Display + in-mission C2 | battlespace-manager → sim/o-my | overlay + TaskCommand |
| 6 | Record | bus → o-my-debrief | tap new topics |

---

## Hop 0 — Shared topics

Add these constants to `uci_common.topics` in **o-my** and **o-my-sim** (planner already has them in `src/omy_mission_plan/topics.py`). Strings MUST match exactly.

### Mission planning

| Constant | Topic | MessageType |
|----------|-------|-------------|
| `TOPIC_MISSION_PLAN` | `uci.mission.plan` | `MissionPlan` |
| `TOPIC_MISSION_PLAN_COMMAND` | `uci.mission.plan.command` | `MissionPlanCommand` |
| `TOPIC_MISSION_PLAN_STATUS` | `uci.mission.plan.status` | `MissionPlanStatus` |
| `TOPIC_MISSION_PLAN_ACTIVATION` | `uci.mission.plan.activation` | `MissionPlanActivation` / `MissionPlanActivationCommand` |
| `TOPIC_MISSION_PLAN_ACTIVATION_STATUS` | `uci.mission.plan.activation.status` | `MissionPlanActivationStatus` |
| `TOPIC_MISSION_PLAN_EXECUTION` | `uci.mission.plan.execution` | `MissionPlanExecutionStatus` |
| `TOPIC_MISSION_PLAN_VALIDATION` | `uci.mission.plan.validation` | `MissionPlanValidationCommand` |
| `TOPIC_ROUTE_PLAN` | `uci.route.plan` | `RoutePlan` |
| `TOPIC_TASK_PLAN` | `uci.task.plan` | `TaskPlan` |
| `TOPIC_ROUTE_ACTIVITY_PLAN` | `uci.route.activity.plan` | `RouteActivityPlan` |
| `TOPIC_TASK_COMMAND` | `uci.task.command` | `TaskCommand` |
| `TOPIC_TASK_CANCEL` | `uci.task.cancel` | `TaskCancelCommand` |
| `TOPIC_ROUTE_MODIFICATION` | `uci.route.modification` | `RouteModificationRequest` |
| `TOPIC_REQUIREMENT_SET` | `uci.requirement.set` | `RequirementSet` |

### EOB / OOB distro

| Constant | Topic | MessageType |
|----------|-------|-------------|
| `TOPIC_ORDER_OF_BATTLE` | `uci.oob` | `OrderOfBattle` |
| `TOPIC_ORDER_OF_BATTLE_REQUEST` | `uci.oob.request` | `OrderOfBattleRequest` |
| `TOPIC_WORKING_EOB` | `uci.eob.working` | `WorkingEOB` |
| `TOPIC_EOB_CORRELATION` | `uci.eob.correlation` | `EOB_CorrelationRecord` |

### F2T2EA catalog (beyond existing program topics)

| Constant | Topic | MessageType | Maps to existing |
|----------|-------|-------------|------------------|
| `TOPIC_PRIORITIZATION` | `uci.prioritization` | `Prioritization` | beads `o-my-w17.1` (`uci.target.priority_list`) — **prefer catalog name** |
| `TOPIC_DMPI` | `uci.dmpi` | `DMPI` | Target phase aimpoint |
| `TOPIC_DMPI_DESIGNATION` | `uci.dmpi.designation` | `DMPI_Designation` | |
| `TOPIC_DMPI_STATUS` | `uci.dmpi.status` | `DMPI_Status` | |
| `TOPIC_EFFECT_PLAN` | `uci.effect.plan` | `EffectPlan` | weaponeering / desired effect |
| `TOPIC_ACTION_PLAN` | `uci.action.plan` | `ActionPlan` | MissionPlan sub-plan |
| `TOPIC_STRIKE_CONSENT` | `uci.strike.consent` | `StrikeConsentRequest` | ROE / CDE gate |
| `TOPIC_DAMAGE_ASSESSMENT_REQUEST` | `uci.assessment.damage.request` | `DamageAssessmentRequest` | Assess / BDA |

Existing o-my F2T2EA topics stay: `uci.intel.product`, `uci.threat.assessment`, `uci.target.generated`, `uci.target.allocated`, `uci.target.status`, `uci.engagement.result`, `uci.f2t2ea.state`.

---

## Hop 1 — EOB working set (fuzzy-reconciler → planner + sim)

**Identity space:** `Entity.id` is stable across `gulf_base.json` (planned OOB) and `gulf_delta.json` (live detections). Planner consumes **base** only. Sim detections consume **delta** only. Never mix geometries.

### 1a. Region JSON (already shipped; extend with EOB profile)

**Publisher:** fuzzy-reconciler working-set / regional fixture export  
**Consumer:** o-my-mission-plan `POST /api/region/ingest`; o-my-sim gulf import (#18)

| Field | Required | Publisher send | Consumer ingest |
|-------|----------|----------------|-----------------|
| `id` | yes | Stable string; becomes `EntityID` / `Threat.entity_id` | Persist; never rewrite |
| `name` | yes | Human label | Display + Task.target_name |
| `lat`, `lon` | yes | WGS-84 decimal degrees | Threat + published mission waypoint |
| `category` | yes | One of: `sam_site`, `surveillance_radar`, `early_warning_radar`, `ballistic_missile_site`, `coastal_defense`, `command_post`, `elint_site` (airports ignored by planner) | Filter via `FIXED_THREAT_CATEGORIES` |
| `analyzed_at` | yes | ISO-8601 | Provenance; OOB timestamp |
| `attributes.range_km` | no | Numeric | Threat ring |
| `attributes.band` | no | RF band string | ELINT cue |
| `attributes.status` | no | `operational` \| `degraded` \| `standby` \| `offline` | Severity |

**EOB profile reserved attributes** (GitHub fuzzy-reconciler **#16** — first-class or reserved keys; do not collide):

| Reserved key | A-GRA source | Required for EOB hop | Planner use | Sim use |
|--------------|--------------|----------------------|-------------|---------|
| `eob_record_id` | `EOB_RecordID` | yes when exporting WorkingEOB | Join to `OrderOfBattle` record | Correlation to SignalReport |
| `elnot` | `ELNOT_Identifier` | preferred | Identity; planning override MUST NOT mutate OOB | ESM cue match |
| `be_number` | BE Number | preferred | Site identity | Same |
| `o_suffix` | `O_Suffix` | preferred with BE | Site identity | Same |
| `site_pin` | `EOB_SitePIN` | no | Display | Display |
| `evaluation_code` | `EOB_CodesType` 1–10 | no | Confidence | Fusion weight |
| `country_code` | CountryCode | no | Filter | Filter |
| `mobility` | `MobilityEnum` | no | `fixed` default for this planner | Relocated delta → treat as mobile/popup |
| `operational_status` | `SiteOperationalStatus` | no | Same as `attributes.status` if both present: `operational_status` wins | Same |

**Must persist:** `id`, EOB identity keys, lat/lon, category.  
**Ignore OK:** `original_row`, UI-only reconcilation fields.

### 1b. WorkingEOB / OrderOfBattle XML (prototype: HTTP export)

**Publisher:** fuzzy-reconciler `POST /api/export/oob` **or** o-my-mission-plan wrapping ingested JSON (`GET /api/uci/export` key `OrderOfBattle`)  
**Consumer:** o-my (EOB store), o-my-sim (known OB layer), battlespace-manager (static threat overlay)

Topic `uci.oob` / `uci.eob.working`. CorrelationID = `OrderOfBattleID`.

| Field | Required | Notes |
|-------|----------|-------|
| `OrderOfBattleID` | yes | Stable per working set version |
| `Name` | yes | e.g. `GULF-BASE-EOB` |
| `ValidFrom` | yes | From fixture `analyzed_at` min or export time |
| `OpZone` | no | Bounding box of entities |
| `Record[]/EOB_RecordID` | yes | = `attributes.eob_record_id` or `id` |
| `Record[]/EntityID` | yes | = JSON `id` |
| `Record[]/Name` | yes | |
| `Record[]/Position/Latitude` `Longitude` | yes | |
| `Record[]/Category` | yes | fuzzy category |
| `Record[]/ELNOT` | no | |
| `Record[]/BE_Number` `O_Suffix` | no | |
| `Record[]/EvaluationCode` | no | |
| `Record[]/Mobility` | no | default `FIXED` |
| `Record[]/OperationalStatus` | no | |
| `Record[]/Kind` | yes | `EmitterRecord` \| `MissileRecord` \| `FacilityRecord` \| `LandRecord` |

UCI also allows `Entity` as a **pre-briefed OOB object** (HUMINT / EOB, not a live fused track). When publishing OOB, also emit `uci.entity` with `Perspective=PREBRIEFED` (or `mp:Source=EOB`) so COP can draw the planned laydown without waiting for sensors.

**OOB update:** republish `OrderOfBattle` with incremented version. o-my SHALL then publish `MissionPlanValidationCommand` (reason `ORDER_OF_BATTLE`) so the planner revalidates affected MissionPlans. Do not silently mutate a live RoutePlan.

---

## Hop 2 — Deliberate MissionPlan (o-my-mission-plan → sim + o-my)

**Publisher:** o-my-mission-plan (`GET /api/uci/export` and bus publish on launch)  
**Consumers:** o-my-sim (activate/fly), o-my (plan-monitor cache), battlespace-manager (dashed planned overlay), o-my-debrief (record)

CorrelationID = `MissionPlanID` on **every** message in the thread.

### 2a. MissionPlan (`uci.mission.plan`)

| Field | Required | Publisher | Consumer must persist |
|-------|----------|-----------|------------------------|
| `MissionPlanID` | yes | UUID / `MP-…` | Join key |
| `Name` | yes | Option label | Display |
| `SystemID` | yes | Package id `PKG-1` | Package grouping |
| `Region` | no | `gulf` | Filter |
| `SubPlans/RoutePlanID[]` | yes | One per assigned platform | Load routes |
| `SubPlans/TaskPlanID[]` | yes | One per assigned platform | Load tasks |
| `SubPlans/RouteActivityPlanID[]` | yes | Tie tasks to waypoints | Execute offsets |
| `ExecutionOrder[]` | yes | `INGRESS → SEAD → ISR → STRIKE → EGRESS` | Sequence gate |
| `ThreatEntityID[]` | yes | fuzzy `id`s planned against | Overlay + validation |
| `OrderOfBattleID` | no until hop 1b | Link to EOB used | Revalidate on OOB update |
| `RequirementSetID` | no | Ready-for-planning gate | |

UCI rule: sub-plans activate/execute **only** as part of this MissionPlan.

### 2b. RoutePlan (`uci.route.plan`)

| Field | Required | Publisher | Consumer |
|-------|----------|-----------|----------|
| `RoutePlanID` | yes | Persist | Versioned; in-mission edit → new ID.Version |
| `PlatformID` | yes | Aircraft id | Who flies it |
| `RouteName` | yes | Also copied to `PlatformStatus.route_name` | Join live kinematics |
| `Pattern` | yes | `transit` | o-my-sim interpolator |
| `SpeedKts` | no | Default 420 | Kinematics |
| `Waypoint[]/Name` | yes | Published fix name (never `PROX-*`) | Labels |
| `Waypoint[]/Latitude` `Longitude` | yes | WGS-84 | Fly |
| `Waypoint[]/AltitudeFeet` | yes | |
| `Waypoint[]/ETAMinutes` | no | From T+0 | Timeline |

### 2c. TaskPlan (`uci.task.plan`)

| Field | Required | Publisher | Consumer |
|-------|----------|-----------|----------|
| `TaskPlanID` | yes | Persist | |
| `PlatformID` | yes | | |
| `Task[]/TaskID` | yes | | Status join |
| `Task[]/Role` | yes | `ISR` \| `COLLECTION` \| `STRIKE` \| `SEAD` \| `CAS` \| `CAP` \| `EW` | Allocator / display |
| `Task[]/TargetEntityID` | yes | fuzzy `id` | EOB join |
| `Task[]/AssignedPlatformID` | yes | | |
| `Task[]/Priority` | yes | 1 = highest | F2T2EA / JIPTL seed |
| `Task[]/Latitude` `Longitude` | yes | Target loc | |
| `Task[]/TargetName` `TargetType` | no | | |
| `Task[]/StartOffsetMinutes` | no | | RouteActivity fallback |
| `Task[]/PredecessorTaskID[]` | no | SEAD before STRIKE | Gate |
| `Task[]/TimeSensitive` | no | bool | TST |

### 2d. RouteActivityPlan (`uci.route.activity.plan`)

| Field | Required | Consumer |
|-------|----------|----------|
| `RouteActivityPlanID` | yes | |
| `RoutePlanID` | yes | |
| `PlatformID` | yes | |
| `Activity[]/ActivityID` | yes | |
| `Activity[]/TaskID` | yes | |
| `Activity[]/WaypointName` | yes | Must exist on the RoutePlan |
| `Activity[]/OffsetMinutes` | yes | When to emit TaskStatus IN_PROGRESS |
| `Activity[]/Action` | yes | `EXECUTE_TASK` |

### 2e. MissionPlanStatus (`uci.mission.plan.status`)

| Field | Required | Values |
|-------|----------|--------|
| `MissionPlanID` | yes | |
| `State` | yes | `PLANNED` \| `CONVERTING` \| `UPLOADING` \| `ACTIVATING` \| `ACTIVE` \| `INVALID` \| `ABORTED` |
| `Detail` | no | Human reason |

### 2f. JSON companion (already shipped)

Topic `uci.route` / file export `o-my.mission-plan.routes/v1` remains valid for o-my-sim until XML ingest lands. After hop 3, XML MissionPlan is authoritative; JSON is a convenience adapter.

---

## Hop 3 — Activate and fly (o-my-sim)

**Publisher:** o-my-sim scenario-director + platform-status-sim  
**Consumers:** o-my plan-monitor, battlespace-manager, o-my-debrief

### 3a. MissionPlanActivation (`uci.mission.plan.activation`)

May be published by COP, compose, or scenario-director.

| Field | Required |
|-------|----------|
| `MissionPlanID` | yes |
| `Command` | yes — `ACTIVATE` \| `DEACTIVATE` |
| `SimTimeZero` | no — ISO or scenario T+0 |

**ACK** `MissionPlanActivationStatus` on `uci.mission.plan.activation.status`:

| Field | Required |
|-------|----------|
| `MissionPlanID` | yes |
| `Accepted` | yes bool |
| `State` | `ACTIVATING` \| `EXECUTING` \| `REJECTED` |
| `Reason` | required if rejected |

Every Command-2 **must** produce this status (IxDF: feedback is a message).

### 3b. Fly RoutePlan

Sim SHALL interpolate `RoutePlan` waypoints (`pattern: transit`). Do not invent runtime lat/lon. Publish existing `PlatformStatus` **plus** execution:

`PlatformStatus` (`uci.platform.status`) — already exist; **add** these fields consumers need for plan-monitor:

| Field | Required for hop 3 | Notes |
|-------|--------------------|-------|
| `PlatformID` | yes | = RoutePlan.PlatformID |
| `Latitude` `Longitude` `AltitudeFeet` | yes | |
| `RouteName` | yes | = RoutePlan.RouteName |
| `ActiveTaskID` | no | Current TaskPlan task |
| `MissionPlanID` | **yes once activated** | Join |
| `FuelRemaining` | no | Existing |
| `WeaponsRemaining` | no | Existing |

### 3c. MissionPlanExecutionStatus (`uci.mission.plan.execution`)

Published by sim (coarse: EXECUTING/COMPLETE) and **enriched by o-my plan-monitor** (ON_PLAN/OFF_PLAN).

| Field | Required | Values / notes |
|-------|----------|----------------|
| `MissionPlanID` | yes | |
| `PlatformID` | yes | Per-platform messages (not only package rollup) |
| `State` | yes | `PLANNED` \| `ACTIVATING` \| `EXECUTING` \| `ON_PLAN` \| `OFF_PLAN` \| `COMPLETE` \| `ABORTED` |
| `CrossTrackNm` | yes when live | Absolute nm vs RoutePlan |
| `DeviationSeverity` | yes when live | `NONE` \| `WATCH` \| `OFF_PLAN` \| `CRITICAL` |
| `ClosestLeg` | no | `IP→TGT` style |
| `InMissionRetask` | yes | bool — true after accepted TaskCommand |

Thresholds (shared, do not fork): **WATCH 2 nm**, **OFF_PLAN 5 nm**, **CRITICAL 12 nm**.

### 3d. TaskStatus (`uci.task.status`)

Existing message. When flying a TaskPlan, emit `QUEUED → ASSIGNED → IN_PROGRESS → COMPLETE | ABORTED` at RouteActivityPlan offsets. Include `TaskID`, `PlatformID`, `MissionPlanID` (CorrelationID).

### 3e. Gulf base vs delta (issues #18 / #19)

| Layer | File | Who uses geometry |
|-------|------|-------------------|
| Planned OOB | `gulf_base.json` | planner + sim static OB overlay |
| Live detections | `gulf_delta.json` | sim sensors only |

Same `id`. Relocated delta (~80–150 km) → popup / Find-Fix pressure, **not** a silent rewrite of the RoutePlan. Spatial-proximity delta → correlator candidate.

---

## Hop 4 — o-my process (plan-monitor, EOB, F2T2EA)

**Publisher:** o-my services  
**Consumers:** COP, planner (validation), debrief

### 4a. plan-monitor (new)

Subscribe: `uci.mission.plan`, `uci.route.plan`, `uci.platform.status`.  
Publish: `uci.mission.plan.execution` (severity), `uci.threat.notification` kind `PLAN_DEVIATION`.

Notification payload (Attention rail):

| Field | Required |
|-------|----------|
| `Kind` | `PLAN_DEVIATION` |
| `Title` | e.g. `VIPER01 off plan 6.2 nm` |
| `Tone` | `watch` \| `off-plan` \| `critical` |
| `Icon` | `watch` \| `break` \| `alert` |
| `PlatformID` `MissionPlanID` | yes |
| `CrossTrackNm` | yes |
| `EntityID` | no |

Color is never the only cue ([IXDF-FEEDBACK.md](IXDF-FEEDBACK.md)).

### 4b. EOB ingest + validation

Subscribe `uci.oob` / `uci.eob.working` / pre-briefed `uci.entity`. Persist records by `EOB_RecordID` + `EntityID`.

On OOB version bump that intersects `MissionPlan.ThreatEntityID[]`, publish:

**MissionPlanValidationCommand** (`uci.mission.plan.validation`)

| Field | Required |
|-------|----------|
| `MissionPlanID` | yes |
| `Reason` | `ORDER_OF_BATTLE` |
| `OrderOfBattleID` | yes |
| `ChangedEntityID[]` | yes |

Planner responds with `MissionPlanStatus` `INVALID` or a new MissionPlan version. Live kinematics are **not** rewritten in place.

### 4c. F2T2EA — catalog messages to add

Existing program chain stays. Add catalog elements so deliberate + dynamic targeting share IDs:

| Phase | Catalog message | Topic | Seed from |
|-------|-----------------|-------|-----------|
| Find | `WorkingEOB` / `Entity` pre-briefed + `SignalReport` | `uci.eob.working`, `uci.signal.report` | hop 1 |
| Fix | `EOB_CorrelationRecord` | `uci.eob.correlation` | SignalReport ↔ EOB_RecordID |
| Track | `Entity` (fused) | `uci.entity` | existing |
| Target | `Prioritization` (per F2T2EA phase) | `uci.prioritization` | TaskPlan.Priority + `o-my-w17.1` |
| Target | `DMPI` / `DMPI_Designation` | `uci.dmpi*` | strike Task lat/lon |
| Target | `Effect` / `EffectPlan` | `uci.effect.plan` | weaponeering |
| Engage | `StrikeConsentRequest` | `uci.strike.consent` | CDE / `o-my-w17.2` |
| Assess | `DamageAssessmentRequest` + existing `uci.target.status` | `uci.assessment.damage.request` | `o-my-w17.4` |

**Prioritization** (UCI: “priority list per F2T2EA phase, system, time, or space”):

| Field | Required |
|-------|----------|
| `PrioritizationID` | yes |
| `Purpose` | `F2T2EA_TARGET` \| `F2T2EA_FIND` \| `SEAD` \| `JIPTL` |
| `Phase` | `FIND` \| `FIX` \| `TRACK` \| `TARGET` \| `ENGAGE` \| `ASSESS` (optional filter) |
| `Item[]/Rank` | yes 1..n |
| `Item[]/EntityID` | yes |
| `Item[]/TaskID` | no |
| `Item[]/DMPI_ID` | no |
| `MissionPlanID` | no — when seeded from a plan |

Prefer this over inventing `uci.target.priority_list` as a parallel schema. Beads `o-my-w17.1` SHOULD alias to `Prioritization`.

**DMPI** (aimpoint, not the Entity centroid):

| Field | Required |
|-------|----------|
| `DMPI_ID` | yes |
| `TargetEntityID` | yes |
| `Latitude` `Longitude` `ElevationFeet` | yes |
| `WeaponEffect` | no |
| `TaskID` | no |

---

## Hop 5 — COP (battlespace-manager)

**Subscriber only** for operational data. Never system of record.

### 5a. Planned vs actual overlay

| Ingest | Draw |
|--------|------|
| `RoutePlan` | Dashed planned polyline, labeled published waypoints |
| `PlatformStatus` | Solid actual breadcrumb |
| `MissionPlanExecutionStatus` OFF_PLAN/CRITICAL | Break mark + callsign + nm |

### 5b. Attention kinds (add to rail)

Today: `TST`, `POPUP`, `TARGET`, `TASK`, `CUSTODY`, `AGENT`.  
Add: `PLAN_DEVIATION`, `RETASK` — fields as hop 4a. Pair tone + icon + text.

### 5c. In-mission TaskCommand (closes display gap G4)

**Publisher:** battlespace-manager  
**Consumer:** o-my-sim (fly) and/or o-my allocator  
Topic `uci.task.command`. Do **not** HTTP POST to sim `:8018`.

| Field | Required |
|-------|----------|
| `TaskCommandID` | yes |
| `MissionPlanID` | yes CorrelationID |
| `PlatformID` | yes |
| `Role` | yes |
| `TargetEntityID` | yes |
| `Latitude` `Longitude` | yes |
| `Reason` | no |
| `ReplaceTaskID` | no |

ACK: `TaskStatus` + `MissionPlanExecutionStatus.InMissionRetask=true`.  
COP shows Attention `RETASK` until ACK. Rejected → title includes reason.

Kinematic rewrite uses `RouteModificationRequest` (`uci.route.modification`) → new `RoutePlan` version. `[Capability]Command` MUST NOT silently replace the plan.

`TaskCancelCommand` on `uci.task.cancel` with `TaskCancelCommandStatus` ACK (positive cancel; avoids race).

---

## Hop 6 — Debrief recorder

o-my-debrief default topic list SHALL add hop 0 mission + EOB + F2T2EA catalog topics. Persist `MessageType`, `CorrelationID`, `MissionPlanID`, `PlatformID`. Do not require a new schema beyond existing Parquet columns + payload JSON.

---

## Round-trip acceptance (all hops)

A fixture MissionPlan XML from `GET /api/uci/export` plus gulf_base EOB SHALL:

1. Be ingested by o-my-sim without renaming EntityIDs.
2. Produce `PlatformStatus.MissionPlanID` matching the export.
3. Produce `MissionPlanExecutionStatus` that o-my and the COP parse (`State`, `DeviationSeverity`, `CrossTrackNm`).
4. Accept a `TaskCommand` and return `TaskStatus` (never HTTP-only).
5. Survive an OOB update via `MissionPlanValidationCommand` rather than mutating waypoints in place.

Cross-stack test lives in o-my (`scripts/verify-cross-stack-bus.py` or successor) and asserts every **required** field in this document.

---

## Example snippets

### Region entity (hop 1)

```json
{
  "id": "gulf-sam-001",
  "name": "SA-6 Battery Al-Jaber",
  "lat": 29.076,
  "lon": 47.920,
  "analyzed_at": "2026-08-01T00:00:00Z",
  "category": "sam_site",
  "attributes": {
    "range_km": 24,
    "band": "G/H",
    "status": "operational",
    "eob_record_id": "EOB-GULF-SAM-001",
    "elnot": "SA6",
    "be_number": "BE123456",
    "o_suffix": "A",
    "mobility": "FIXED",
    "operational_status": "operational",
    "evaluation_code": 5,
    "country_code": "KU"
  }
}
```

### MissionPlan header (hop 2)

```xml
<uci:Message xmlns:uci="urn:uci:standard:1.0" xmlns:mp="urn:omy:mission:1.0">
  <uci:Header>
    <uci:MessageID>MP-HDR-001</uci:MessageID>
    <uci:Timestamp>2026-08-13T12:00:00Z</uci:Timestamp>
    <uci:Sender>omy-mission-plan</uci:Sender>
    <uci:MessageType>MissionPlan</uci:MessageType>
    <uci:CorrelationID>MP-GULF-001</uci:CorrelationID>
  </uci:Header>
  <!-- mp:MissionPlan with SubPlans + ExecutionOrder + ThreatEntityID -->
</uci:Message>
```
