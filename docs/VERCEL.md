# Deploying on Vercel

The public demo boots with the **bundled fuzzy-reconciler Gulf War EOB**
(`fixtures/regions/gulf_threats.json`): fixed IADS threats from the Gulf theater,
ingested at startup and planned automatically.

| Concern | Demo behavior |
|---------|----------------|
| API | Stateless FastAPI serverless function (`api/index.py`) |
| UI | Vanilla static assets served by FastAPI (`/` + `/assets/*`) |
| Gulf EOB | Auto-ingested on boot when `VERCEL=1` (override with `INGEST_GULF_EOB`) |
| Session state | In-memory per instance — cold starts reset; fine for demo |

## Deploy (GitHub → Vercel)

1. Push `main` to [mowgli42/o-my-mission-plan](https://github.com/mowgli42/o-my-mission-plan).
2. In [Vercel](https://vercel.com/new): **Add New Project** → Import the GitHub repo.
3. Leave settings at defaults from `vercel.json` / `pyproject.toml`:
   - **Root Directory:** repository root (`.`)
   - **Install:** `pip install .`
   - **Entrypoint:** `[tool.vercel] entrypoint = "api.index:app"`
4. No secrets required for the demo.
5. Deploy. Production URL serves UI + `/api/*` same-origin.

### Post-deploy smoke checks

```bash
curl -s https://YOUR_PROJECT.vercel.app/api/health
# expect: gulf_eob_bootstrapped=true, plan_ready=true

curl -s https://YOUR_PROJECT.vercel.app/api/uci/export | head -c 200
# expect: MissionPlan + OrderOfBattle XML keys

curl -s -o /dev/null -w '%{http_code}' https://YOUR_PROJECT.vercel.app/
curl -s -o /dev/null -w '%{http_code}' https://YOUR_PROJECT.vercel.app/assets/app.js
```

Re-ingest manually (optional):

```bash
curl -s -X POST https://YOUR_PROJECT.vercel.app/api/region/ingest \
  -H 'Content-Type: application/json' \
  -d '{"max_threats": 16, "run_plan": true}'
```

## Deploy (CLI)

```bash
npx vercel link    # once
npx vercel         # preview
npx vercel --prod  # production
```

## What the build bundles

| Asset | Source |
|-------|--------|
| Python app | `pip install .` → `src/omy_mission_plan/` |
| Gulf EOB fixture | `fixtures/regions/gulf_threats.json` via `includeFiles` |
| Static UI | `src/omy_mission_plan/static/` via `includeFiles` |
| Optional nav extract | `data/nav/gulf-earth_nav.dat` when `NAV_SOURCE=xplane` |

## Optional env

| Variable | Purpose |
|----------|---------|
| `VERCEL` | Set automatically; enables path-recovery middleware + export defaults |
| `INGEST_GULF_EOB` | `1` (default on Vercel) ingests Gulf fixture at boot; `0` for demo world only |
| `ROUTE_SUPPLIER` | `fallback` (default), `openroutefinder`, or `costgrid` |
| `NAV_SOURCE` | `fixture` (default) or `xplane` |

## Do not use catch-all rewrites

Avoid `{ "source": "/(.*)", "destination": "/api/index" }` — it can collapse ASGI
paths and break FastAPI routing. This app serves UI and API from the same function.

## Local parity

```bash
make demo
# open http://localhost:8000
```

Simulate Vercel boot locally:

```bash
INGEST_GULF_EOB=1 make demo
```
