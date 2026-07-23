# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd prime` for full workflow context.

> **Architecture in one line:** Issues live in a local Dolt database
> (`.beads/dolt/`); cross-machine sync uses `bd dolt push/pull`.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work atomically
bd close <id>         # Complete work
bd dolt push          # Push beads data to remote
```

## Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists.
- Follow `openspec/WORKFLOW.md` strictly: OpenSpec → Beads → Implement → Validate.
- Prefer one Beads issue at a time.
- Keep the Route Propagation Service small and focused on fuel/leg feasibility.
- External suppliers (rich ATO, advanced allocation, loadouts) will talk via UCI messages — design contracts, do not implement the full services in this repo.

## Session Completion

When ending a work session:

1. File issues for remaining work
2. Run quality gates if code changed
3. Update issue status
4. `git pull --rebase && git push`
5. Hand off context for next session
