# UCI 2.5 message interactions

Catalog names from Open Arsenal UCI 2.5 (`UCI_MessageDefinitions_v2_5_0.xsd`).  
Tier B bodies: `urn:uci:standard:1.0` header + `urn:omy:mission:1.0` payload.  
`CorrelationID` = `MissionPlanID` on every message in a mission thread.

UCI rule used throughout: **sub-plans (`RoutePlan`, `TaskPlan`, `RouteActivityPlan`, `ActionPlan`, …) can only be activated and executed as part of a `MissionPlan`.** In-mission `[Capability]Command` messages are *not* supposed to rewrite the kinematic plan; `TaskCommand` + `RouteModificationRequest` are the explicit retask path, and they always produce status.

---

## Message set (this flow)

### Planning (o-my-mission-plan publishes)

| UCI 2.5 element | Primitive | Topic | Purpose |
|-----------------|-----------|-------|---------|
| **MissionPlan** | Data-1 | `uci.mission.plan` | Aggregate of sub-plans + execution order for one package / system |
| **RoutePlan** | Data-1 | `uci.route.plan` | WGS-84 waypoints for one platform |
| **TaskPlan** | Data-1 | `uci.task.plan` | Planned tasks (role, target, predecessors, TOT) |
| **RouteActivityPlan** | Data-1 | `uci.route.activity.plan` | Tie tasks to route waypoints / offsets |
| **MissionPlanCommand** | Command-2 | `uci.mission.plan.command` | Invoke / constrain planning (“what-if” threat add/remove) |
| **MissionPlanStatus** | Status-1 | `uci.mission.plan.status` | Planning / conversion / upload / activation chain |

### Activation (operator or control plane)

| UCI 2.5 element | Primitive | Topic | Purpose |
|-----------------|-----------|-------|---------|
| **MissionPlanActivation** / **MissionPlanActivationCommand** | Command-2 | `uci.mission.plan.activation` | Start execution of the MissionPlan and its sub-plans |
| **MissionPlanActivationStatus** | Command-2 / Status-1 | `uci.mission.plan.activation.status` | ACK — accepted, rejected, why |

### Execution (o-my-sim publishes; o-my may enrich)

| UCI 2.5 element | Primitive | Topic | Purpose |
|-----------------|-----------|-------|---------|
| **MissionPlanExecutionStatus** | Status-1 | `uci.mission.plan.execution` | Per-platform ON_PLAN / OFF_PLAN / COMPLETE; cross-track error |
| **TaskStatus** | Status-1 | `uci.task.status` | QUEUED → ASSIGNED → IN_PROGRESS → COMPLETE / ABORTED |
| **PlatformStatus** *(program; maps toward SystemStatus / kinematics)* | Status-1 | `uci.platform.status` | Lat/lon, fuel, weapons, `route_name`, `active_task_id` |
| **RouteDefinition** *(program; RoutePlan snapshot on the live bus)* | Data-1 | `uci.platform.route` | Waypoints o-my already consumes |
| **Entity** | Data-1 | `uci.entity` | Fused track / fixed site |
| **EntityNotification** | Data-1 | `uci.entity.notification` | Classification |
| **SignalReport** | Data-1 | `uci.signal.report` | SIGINT/IMINT cue on a fixed site |
| **RawTrackUpdate** *(program)* | Data-1 | `uci.raw.track` | Sensed kinematics |

### In-mission C2 (battlespace-manager publishes; sim/o-my ACK)

| UCI 2.5 element | Primitive | Topic | Purpose |
|-----------------|-----------|-------|---------|
| **TaskCommand** | Command-2 | `uci.task.command` | Assign / change a task *during* execution without silently mutating MissionPlan |
| **TaskCancelCommand** + **TaskCancelCommandStatus** | Command-2 | `uci.task.cancel` | Positive cancel feedback (UCI exists specifically to avoid race conditions) |
| **RouteModificationRequest** + **RouteModificationRequestStatus** | ActionRequest-2 | `uci.route.modification` | Atomic route edit; result is a **new** `RoutePlan` with incremented version |
| **Task** *(o-my allocator product)* | Data-1 | `uci.task` | Dynamic allocation (ISR/SEAD/STRIKE) on top of the deliberate TaskPlan |

### EOB / OOB distro (fuzzy-reconciler and/or planner publish)

| UCI 2.5 / A-GRA element | Primitive | Topic | Purpose |
|-------------------------|-----------|-------|---------|
| **OrderOfBattle** | DataRecord-1 | `uci.oob` | Versioned units/sites/equipment/threats in a volume |
| **OrderOfBattleRequest** (+ status) | ActionRequest-2 | `uci.oob.request` | On-demand subset by OpZone |
| **WorkingEOB** / **WorkingEOB_Request** | A-GRA | `uci.eob.working` | Working subset of EOB |
| **EOB_CorrelationRecord** | A-GRA | `uci.eob.correlation` | SignalReport / Entity → EOB_RecordID |
| **Entity** (pre-briefed OOB) | Data-1 | `uci.entity` | HUMINT/EOB object, not a live fused track |
| **MissionPlanValidationCommand** | Command-2 | `uci.mission.plan.validation` | Revalidate plan when OOB changes |

### F2T2EA catalog (o-my; planner may seed)

| UCI 2.5 element | Primitive | Topic | Purpose |
|-----------------|-----------|-------|---------|
| **Prioritization** | DataRecord-1 | `uci.prioritization` | Priority list **per F2T2EA phase**, system, time, or space (alias beads `o-my-w17.1`) |
| **RequirementSet** | Data-1 | `uci.requirement.set` | Ready-for-planning / JIPCL-lite |
| **DMPI** / **DMPI_Designation** / **DMPI_Status** | Data / Command | `uci.dmpi*` | Aimpoint distinct from Entity centroid |
| **EffectPlan** / **ActionPlan** | Data-1 | `uci.effect.plan`, `uci.action.plan` | Desired effect + action sub-plans |
| **StrikeConsentRequest** | ActionRequest-2 | `uci.strike.consent` | ROE / CDE gate before Engage |
| **DamageAssessmentRequest** | ActionRequest-2 | `uci.assessment.damage.request` | Assess / BDA request |

### Operator attention (o-my publishes; display subscribes)

| Element | Topic | Maps to Attention Rail |
|---------|-------|------------------------|
| **ThreatNotification** (program) | `uci.threat.notification` | TST / POPUP / TARGET today; **PLAN_DEVIATION**, **RETASK** added |
| **RouteThreatAssessment** | `uci.route.threat` | Route exposure |
| **SystemNotification** (catalog) | optional later | System-level alerts |

Normative send/ingest tables: [UCI-CONTRACTS.md](UCI-CONTRACTS.md). Unused catalog that we **should** use: [UCI-GAPS.md](UCI-GAPS.md).

---

## Mapping from existing OMY-GW-1 names

| Demo / o-my-sim today | UCI 2.5 |
|-----------------------|---------|
| `TrackReport` | `Entity` |
| `CategorizedEntity` | `EntityNotification` |
| `PlatformStatusReport` | kinematics + `SystemStatus` subset; keep program `PlatformStatus` at Tier B |
| `Task` / `TaskAllocation` | `Task` in a `TaskPlan`, or live `Task` from allocator |
| `TaskStatus` | `TaskStatus` |
| `RouteDefinition` | live geometry derived from `RoutePlan` |
| scenario `TASK_REQUEST` | `TaskCommand` or `MissionPlanCommand` constraint |

---

## Interaction patterns (Normalized Interface)

UCI NIS primitives used here:

| Pattern | When |
|---------|------|
| **Data-1** pub/sub | Plans, entities, route geometry, execution snapshots |
| **Command-2** command + status | Activation, TaskCommand, TaskCancel, plan command |
| **Status-1** | MissionPlanStatus, ExecutionStatus, TaskStatus |
| **ActionRequest-2** | RouteModificationRequest (atomic in-mission route change) |

Every Command-2 **must** produce a status. That is the machine-level implementation of IxDF feedback.

---

## Correlation

```
MissionPlanID  ==  Header.CorrelationID
RoutePlanID / TaskPlanID / TaskID referenced from MissionPlan
PlatformID on RoutePlan, TaskPlan, PlatformStatus, ExecutionStatus
EntityID on Task.target and fuzzy-reconciler entity.id
```

battlespace-manager and o-my-debrief join the thread on `CorrelationID`.

---

## Sample MissionPlan (Tier B)

See generated files under `out/uci-xml/` after `omy-mission-plan --region gulf`. Root elements:

- `uci:Message/uci:Header/uci:MessageType` = `MissionPlan` | `RoutePlan` | `TaskPlan` | `RouteActivityPlan` | `MissionPlanExecutionStatus` | `TaskCommand`
- `mp:MissionPlan/mp:SubPlans` lists the child plan IDs
- `mp:ExecutionOrder` = `INGRESS → SEAD → ISR → STRIKE → EGRESS` (SEAD predecessors on STRIKE tasks)
