# UCI / A-GRA gaps — mission planning, EOB, F2T2EA

Catalog messages that **support this mission** but are missing or only loosely aliased in current specs and GitHub issues. Pair with [UCI-CONTRACTS.md](UCI-CONTRACTS.md) (normative field tables) and [UCI-MESSAGE-INTERACTIONS.md](UCI-MESSAGE-INTERACTIONS.md) (what we already named).

Sources: Open Arsenal UCI 2.5 `UCI_MessageDefinitions_v2_5_0.xsd`; A-GRA v5.0a `A-GRA_MessageDefinitions_v5_0_a.xsd`.

---

## Already in specs (do not re-open)

| Element | Where |
|---------|--------|
| `MissionPlan`, `RoutePlan`, `TaskPlan`, `RouteActivityPlan` | o-my-mission-plan R22, export API |
| `MissionPlanStatus`, `MissionPlanExecutionStatus`, `TaskCommand` | R23, IxDF feedback |
| `Entity`, `EntityNotification`, `SignalReport`, `PlatformStatus` | o-my / o-my-sim bus |
| Program F2T2EA: intel / threat / target.* / engagement / `uci.f2t2ea.state` | o-my `F2T2EA_PLAN.md` |
| Beads `o-my-w17.*` (JIPTL-lite, CDE, TDN, BDA II/III, NSL/RTL, JIPCL, MIDB, cyber) | o-my AFDP scorecard — **map to catalog names below** rather than parallel schemas |

---

## EOB / OOB distro and update

UCI: *Order of Battle includes units, sites, equipment, and all known threats in a volume.* A-GRA adds working-set and correlation records. Fuzzy-reconciler **#16** lists identity fields but not the **distribution protocol**.

| Gap | Catalog | Why it matters | Spec / issue action |
|-----|---------|----------------|---------------------|
| No OOB message on the bus | **`OrderOfBattle`** (DataRecord-1) | Planner, sim, COP, and fusion need one versioned laydown, not a private JSON file | Hop 1b contract; FR export + planner republish |
| No request/response for a volume | **`OrderOfBattleRequest`** / **`OrderOfBattleRequestStatus`** | On-demand subset (OpZone) instead of dumping 300 sites | Optional after first publish |
| No working-set bounded by zone | A-GRA **`WorkingEOB`**, **`WorkingEOB_Request`** | CAOC “current EOB in Kuwait box” | FR export; o-my store |
| No SIGINT↔site join | A-GRA **`EOB_CorrelationRecord`** | Fix phase: SignalReport ELNOT → EOB record | o-my Fix; sim #19 detections |
| Entity used only as live track | **`Entity` as pre-briefed OOB** (HUMINT/EOB) | COP can draw planned IADS before sensors | Publish with `Source=EOB` |
| OOB records not typed | **`EmitterRecord`**, **`MissileRecord`**, **`FacilityRecord`**, **`LandRecord`**, **`AirRecord`** | SAM vs BM vs C2 semantics for SEAD vs STRIKE | Map from fuzzy `category` |
| Planning mutates EOB | UCI planning **overrides** (e.g. override ELNOT on an EOB Entity during planning) | What-if without corrupting the OOB | MissionPlanCommand constraint; never write back to FR |
| Plan not revalidated when OOB changes | **`MissionPlanValidationCommand`** | Explicit UCI reason: order of battle invalidates plans | o-my on OOB version bump |
| Identity keys stuffed in `attributes` only | A-GRA `EOB_RecordID`, ELNOT, BE, O_Suffix, evaluation/function/activity/country, mobility, operational status | Matching and fusion | FR **#16** — do not duplicate; extend with export |

---

## Mission planning (beyond current MissionPlan export)

| Gap | Catalog | Why | Action |
|-----|---------|-----|--------|
| No invoke/constrain planning | **`MissionPlanCommand`** | “What-if: add this threat” / replan | Planner ingest + status |
| No formal activate | **`MissionPlanActivation`** / **`MissionPlanActivationStatus`** | Named in ARCHITECTURE; not implemented in sim | Sim hop 3 |
| No ready-for-planning gate | **`RequirementSet`**, **`CoordinatedRequirementSet`** | Tasks exist; UCI wants requirements approved before plan | Planner stub + o-my JIPCL (`o-my-w17.6`) |
| Effects not first-class | **`Effect`**, **`EffectPlan`** | Weaponeering / desired effect vs a Task role string | F2T2EA Target |
| Actions not first-class | **`Action`**, **`ActionPlan`** | Sub-plan sibling of Route/Task | Optional after EffectPlan |
| No aimpoints | **`DMPI`**, **`DMPI_Designation`**, **`DMPI_DesignationRequest`**, **`DMPI_Status`**, **`DMPI_CancelCommand`** | Strike Task uses entity centroid; BDA needs DMPI | o-my + planner |
| In-mission route edit unnamed | **`RouteModificationRequest`** / **Status** | Architecture mentions it; no field table | Hop 5c |
| Cancel without ACK | **`TaskCancelCommand`** / **Status** | UCI exists to avoid race conditions | Hop 5c |
| No package object | **`PackageDefinition`**, **`PackageStatus`** | MissionPlan `SystemID=PKG-1` is a string only | Later; MissionPlan is enough for v1 |
| No ATO trace | **`OrdersMetadata`** | Trace MissionPlan to ATO | Non-goal until ATO adapter |
| No plan scoring | **`PlanScores`** / **`PlanScoresRequest`** | COA compare exists in planner UI only | Optional; Mission Options stay internal |
| No atomic multi-plan edit | **`PlanModificationRequest`** | Batch version bump | After RouteModificationRequest |
| Station-keeping vs program status | **`PositionReport`**, **`SystemStatus`**, **`NavigationReport`** | We use program `PlatformStatus` | Keep Tier B; map later |

---

## F2T2EA / dynamic targeting

o-my already has a **program** kill-chain on Redis. Gaps are **catalog** messages that make that chain interoperable with the MissionPlan and EOB, plus AFDP items that were beads-only.

| Gap | Catalog / topic | Phase | Existing bead | Action |
|-----|-----------------|-------|---------------|--------|
| Priority list is not UCI `Prioritization` | **`Prioritization`** — “order/priority … including **per F2T2EA phase**, system, time, or space” | Target | `o-my-w17.1` `uci.target.priority_list` | **Alias to `Prioritization`**; do not ship two schemas |
| No DMPI | DMPI series | Target / Engage / Assess | — | New |
| No strike consent | **`StrikeConsentRequest`** | Engage | overlaps `o-my-w17.2` CDE | Gate before `uci.target.allocated` |
| BDA request not catalog | **`DamageAssessmentRequest`** | Assess | `o-my-w17.4` | Pair with `uci.target.status` BdaPhase |
| Collection req not catalog | UCI collection / **RequirementSet** | Find | `o-my-w17.6` `uci.collection.requirement` | Prefer RequirementSet when planning ISR TaskPlan |
| NSL/RTL | (program `uci.target.restrictions` OK) | Target | `o-my-w17.5` | Keep program; reference from Prioritization filter |
| MIDB/MARS | (program snapshot OK) | Find/Target | `o-my-w17.7` | OOB/`OrderOfBattle` is the **site** picture; repository remains target-folder |
| Nomination | (program TDN) | Target | `o-my-w17.3` | May wrap as TaskCommand + Prioritization update |
| Product download | `ProductDownloadRequest` / Download Task | Find | — | Out of scope (no onboard product store) |
| Capability commands vs tasks | `[Capability]Command` | Engage | — | **Must not** rewrite RoutePlan (already in ARCHITECTURE) |

---

## Spec / issue coverage matrix

| Message | omp spec | FR spec | sim spec | o-my spec | COP spec | GH |
|---------|----------|---------|----------|-----------|----------|-----|
| Region JSON + EOB keys | R21, R24 | EOB profile | gulf import | — | — | FR #16 |
| WorkingEOB / OrderOfBattle | R24 | EOB export | known OB layer | EOB ingest | static overlay | **new** |
| MissionPlan bundle | R22 | — | ingest/fly | subscribe | dashed route | omp export done; **sim/o-my new** |
| MissionPlanCommand / Activation / Validation | R25 | — | activation ACK | validation on OOB | activate control | **new** |
| RequirementSet | R25 | — | — | JIPCL map | — | w17.6 + **new** |
| ExecutionStatus + PLAN_DEVIATION | R23 | — | publish coarse | plan-monitor | Attention + overlay | **new** (COP/o-my) |
| TaskCommand / Cancel / RouteModification | R23, R26 | — | honor + ACK | allocator | publish (G4) | BM #14 comment + **new** |
| Prioritization | R27 | — | — | alias w17.1 | optional list | **new** + w17.1 |
| DMPI / EffectPlan | R27 | — | fly to DMPI if present | Target/Assess | map marker | **new** |
| EOB_CorrelationRecord | — | — | SignalReport from delta | Fix | — | **new** |
| StrikeConsent / DamageAssessmentRequest | — | — | — | w17.2 / w17.4 | — | map beads |

---

## Explicitly out of scope (do not file as blockers)

- Full XSD validation (Tier C)
- TBMCS / JADOCS / MIDB as systems of record
- Product download / onboard media URI
- PackageDefinition swarm semantics
- Weather, AAR/tanker geometry, MAPF
- Security markings enforcement
- `[Capability]Command` as a substitute for TaskCommand
