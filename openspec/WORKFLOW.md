# Agent Workflow: OpenSpec + Gherkin + Beads

Follow this order unless the user explicitly requests otherwise.

## 1. Specification (OpenSpec)

- Living capability specs live under `openspec/specs/<capability>/spec.md`.
- Behavior changes use `openspec/changes/<change-id>/` with:
  - `proposal.md` — why + what (include Non-goals)
  - `design.md` — how (decisions, risks)
  - `specs/<capability>/spec.md` — ADDED/MODIFIED requirements with SHALL + GIVEN/WHEN/THEN
  - `tasks.md` — phased checkboxes
  - `verification.md` — scenario → evidence matrix
- Mirror scenarios as `features/*.feature`.
- Validate when CLI available: `npx @fission-ai/openspec validate <change-id> --strict`.

## 2. Task tracking (Beads)

- Create epic + phase children; link with `--spec-id openspec/specs/<capability>/spec.md`.
- Order: demo world + contracts → allocator & route generator → propagation service → dynamic insert → docs/tests.
- Work with `bd ready`; claim with `bd update <id> --claim`; `bd close <id>` when done.

## 3. Implementation

- One Beads issue at a time when practical.
- MVP path: mock tasks + aircraft → simple allocator → navaid route generator → FastAPI propagator (fuel) → dynamic task injection.

## 4. Validation

- Unit tests: `make test`
- Manual: Swagger `/docs` + sample plan cycle

## 5. Archiving

- Merge change deltas into `openspec/specs/<capability>/spec.md` after validate.
