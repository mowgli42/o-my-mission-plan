# Learnings — EOB / Prioritization / DMPI slice (graham-bell)

## Validated

- Ingested EOB reserved keys (`eob_record_id`, `elnot`, BE + O_Suffix) pass through `FixedThreat.attributes` into `OrderOfBattle` XML.
- `Task.target_entity_id` is the fuzzy `id` (not the planner task id). `GET /api/uci/export` TaskPlan `TargetEntityID` matches.
- Airports in the identity fixture are omitted from OOB.
- `POST /api/uci/validate-oob` emits `MissionPlanValidationCommand` reason `ORDER_OF_BATTLE` and leaves RoutePlan waypoint coordinates unchanged.
- STRIKE/SEAD tasks seed catalog `DMPI` + `Prioritization` (`Purpose=F2T2EA_TARGET`). `RequirementSet` is a ready-for-planning stub. `EffectPlan` is an identifier stub (task ids only).

## Not in this slice

- Live Redis publish (HTTP XML only, same as fuzzy-reconciler).
- `MissionPlanCommand` / `MissionPlanActivation` round-trip (sim hop 3).
- Weaponeering on EffectPlan, `StrikeConsentRequest`, `DamageAssessmentRequest`.
- Writing planning overrides back into fuzzy-reconciler (forbidden by contract).
