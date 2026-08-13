# Task Beads — o-my Mission Plan

Issue DB: `.beads/` · prefix `omp` · run `bd ready` / `bd list`.

Local Dolt bootstrap against the configured remote currently fails schema migration (`table has unknown fields`). Until `bd` works here, **`.beads/issues.jsonl` is the source of truth** for this epic.

## Epic `omp-7ak` — MVP planner (mostly closed)

Allocator + route generator + fuel propagator + IxDF UI.

## Epic `omp-uci` — Cross-stack UCI contracts (open) — GH #26

Work **in this order**. Hub: `docs/UCI-CONTRACTS.md`. Gaps: `docs/UCI-GAPS.md`.

| Bead | GH | Focus | Blocks |
|------|----|-------|--------|
| `omp-uci.1` | #27 | EOB profile ingest + `OrderOfBattle` | after fuzzy-reconciler #16 then #19 |
| `omp-uci.2` | #28 | MissionPlanCommand / Activation / Validation / RequirementSet | `.1` |
| `omp-uci.3` | #29 | Seed `Prioritization` + `DMPI` + EffectPlan | `.2` |
| `omp-uci.4` | #30 | Cross-stack required-field test | `.3` (last) |

Sibling beads (other repos): `fr-osm` → `fr-76d`; `o-my-sim-u1n.1` → `.2` → `.3`; `o-my-59k.1` → `.2` → `.3`; `battlespace-manager-5xt.1` → `.2` → `.3`; `omd-50m`.

## Workflow

```bash
bd ready
bd update <id> --claim
bd close <id>
# when Dolt works:
bd dolt push
```
