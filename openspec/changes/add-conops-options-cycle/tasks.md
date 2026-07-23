# Tasks — add-conops-options-cycle

- [x] Merge CONOPS scenarios into living Gherkin (done in features/o-my-mission-plan.feature; keep in sync)
- [x] Update `openspec/specs/o-my-mission-plan/spec.md` with R9 Mission Options, R10 Comparison, R11 Saved router inputs
- [x] Add `MissionOption` (and related) models
- [x] Session/API: create option, list, pin to A/B/C, rerun with patched inputs, compare
- [x] Efficient path uses civil/fallback supplier without forced axis vias
- [x] Unexpected-axis path accepts via list / axis profile and includes those published fixes
- [x] Synchronized path stores sync group + BDA lag metadata for comparison
- [x] Comparison returns GO/NO-GO counts, unallocated count, total distance, emphasis
- [x] Docs already added: CONOPS.md, CIVIL/MISSION route guides, INTEGRATION-GUIDE.md — link from README
- [x] Tests for option persistence, slot pin, compare, rerun
