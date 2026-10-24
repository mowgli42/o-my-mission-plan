# o-my-mission-plan

Mission planning capability for the Open Arsenal / o-my OMS ecosystem. FastAPI + static dark planning UI; published-waypoint routes + fuel propagation for PSAB Gulf War demo. Exports GO routes for o-my-sim and UCI 2.5 MissionPlan XML.

Stack: Python 3.11+ / FastAPI / Pydantic / static Leaflet UI. In-memory demo world. Posture: ponytail (repo >30 days).
Shared health pack lives in `.cursor/skills/` and `.cursor/rules/` — follow those for [Health] work.

## Commands

- Install: `python3 -m pip install -e ".[test]"`
- Test: `make test` or `python3 -m pytest -q`
- Test one file: `python3 -m pytest tests/test_api.py -q`
- Demo / run: `make demo` (http://localhost:8010) or `make run` (with reload)
- Screenshots: `make screenshots` (needs local server)
- Secrets: `bash scripts/scan-secrets.sh .`
- Live: https://o-my-mission-plan.vercel.app (health: `/api/health`)

## Hard prohibitions

- Do not commit private keys, `*-key.pem`, `*.key`, `.env` secrets, or `BEGIN … PRIVATE KEY` blobs. Generate credentials locally; gitignore them.
- Do not invent runtime `PROX-*` lat/lon points. Use only published waypoints (airbases, navaids, fixed mission fixes). See `docs/ROUTE-GENERATION.md`.
- Do not mutate RoutePlan waypoints in place on OOB updates. Validation produces a new MissionPlan version or INVALID status.
- Do not implement full external suppliers (rich ATO, advanced allocation, loadouts) here. Design UCI contracts; keep the Route Propagation Service small.
- Do not rewrite OpenSpec / Gherkin / Beads to match a hoped-for future. Update them only when code already changed.
- Do not invent commands, env vars (`ROUTE_SUPPLIER`, `NAV_SOURCE`), or routes that are not in this tree.

## Verify by change type

| Change | Check |
| --- | --- |
| UI (static) | `make demo` + relevant Plan/Options/Routes screen; `make screenshots` if visuals change |
| API / FastAPI | `python3 -m pytest tests/test_api.py -q` or curl the touched `/api/...` route |
| Spec / Gherkin | matching `features/*.feature` + OpenSpec capability still true; `make test` |
| Deploy | live URL HTTP 200 on `/api/health` and primary plan cycle |
| Secrets / TLS | `bash scripts/scan-secrets.sh .` passes |

## Source of truth

- Behavior: `openspec/specs/o-my-mission-plan/spec.md` + `features/*.feature`
- Remaining work: Beads (`bd`) / GitHub issues
- Demo evidence: README screenshots + `docs/screenshots/` + live Vercel
- Contracts: `docs/UCI-CONTRACTS.md` (normative)
- Health bar: do not duplicate `SUCCESS_CRITERIA.md` here

## House vocabulary

- Mission Option — named plan with emphasis/archetype, router inputs, allocation, routes. Do not call it a "scenario" or "COA" in code (slots A/B/C are the working set).
- Published waypoint — airbase, navaid, or fixed mission fix only. Do not write "generated point" or "PROX-*".
- GO / NO-GO — fuel-reserve feasibility from the propagator. Do not say "valid route" without the fuel check.
- Route Propagation Service — the single source of truth for live routes + fuel state.

## Good / bad (from this repo)

Bad: inventing a runtime lat/lon for a strike that has no nearby published fix.
Good: report the task unsatisfied and keep the route on published fixes only.

Bad: mutating an existing RoutePlan's coordinates when an OrderOfBattle changes.
Good: emit MissionPlanValidationCommand; leave coordinates until a new MissionPlan version is exported.

## Borrowed patterns

- hard-prohibition + single-source from browser-use/browser-use (via ossrules.md) — keep the short rules block separate from long product docs; point at OpenSpec/UCI contracts instead of inlining them.
- verification-matrix from apache/airflow (via ossrules.md) — match the check to the change type (UI vs API vs spec vs deploy).
