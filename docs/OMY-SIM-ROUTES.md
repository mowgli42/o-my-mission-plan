# o-my-sim route import contract

Final planned routes from **o-my-mission-plan** are written so **o-my-sim** can
load them and publish each GO route on the UCI bus when the corresponding
aircraft launches.

## Schema

- **Schema id:** `o-my.mission-plan.routes/v1`
- **UCI topic:** `uci.route`
- **Publish trigger:** `launch.when = "on_aircraft_launch"`

## How to produce an export

```bash
make demo
# then either:
curl -X POST http://localhost:8000/api/plan
curl -X POST http://localhost:8000/api/routes/export
# or use the UI “Export for o-my-sim” button after a plan cycle
```

Files written (default directory `data/routes/`):

| Path | Contents |
|------|----------|
| `<scenario>-routes-latest.json` | Full bundle (overwrite each export) |
| `<scenario>-routes-<UTC>.json` | Timestamped snapshot |
| `aircraft/<aircraft_id>.json` | One file per exported aircraft route |

Committed example (for contract review without running the service):

[`docs/examples/gulf-war-psab-001-routes-example.json`](examples/gulf-war-psab-001-routes-example.json)

## Bundle shape

```json
{
  "schema": "o-my.mission-plan.routes/v1",
  "scenario_id": "gulf-war-psab-001",
  "scenario_name": "Desert Storm — PSAB launch (Kuwait / Iraq)",
  "generated_at": "2026-07-23T01:00:00+00:00",
  "launch_base_id": "OEPS",
  "uci": {
    "route_topic": "uci.route",
    "notes": "o-my-sim loads this file and publishes each GO route on uci.route when the corresponding aircraft launches."
  },
  "summary": { "route_count": 5, "go": 5, "nogo": 0 },
  "routes": [ /* see below */ ]
}
```

## Per-route record (what sim publishes)

```json
{
  "aircraft_id": "FTR-1",
  "callsign": "Viper-1",
  "aircraft_type": "FIGHTER",
  "home_base_id": "OEPS",
  "uci_topic": "uci.route",
  "launch": {
    "when": "on_aircraft_launch",
    "publish": true,
    "launch_base_id": "OEPS"
  },
  "status": "GO",
  "assigned_task_ids": ["STK-01"],
  "unsatisfied_task_ids": [],
  "waypoints": [
    {
      "seq": 0,
      "id": "OEPS",
      "name": "Prince Sultan AB (PSAB) / Al Kharj",
      "kind": "airbase",
      "lat": 24.0627,
      "lon": 47.5805,
      "associated_task_id": null
    }
  ],
  "legs": [],
  "total_distance_nmi": 0.0,
  "feasibility": {
    "go": true,
    "initial_fuel": 20000.0,
    "reserve_fuel": 2500.0,
    "burn_rate_per_nmi": 12.0,
    "final_fuel": 20000.0,
    "infeasible_reason": null
  }
}
```

### Field notes for o-my-sim

| Field | Sim behavior |
|-------|----------------|
| `launch.publish` | Only publish when `true` (GO routes) |
| `launch.when` | Hold until that aircraft’s launch event |
| `waypoints[].seq` | Ordered route for the platform |
| `waypoints[].kind` | `airbase` \| `navaid` \| `mission` — all published |
| `legs` | Optional; useful for fuel / timing displays |
| `feasibility.go` | Must be true for launch publish in the prototype |

## API

| Method | Path | Behavior |
|--------|------|----------|
| POST | `/api/routes/export` | Build + write bundle (`write=true` by default) |
| GET | `/api/routes/export` | Build bundle in-memory (no write) |

Request body (POST, optional):

```json
{ "include_nogo": false, "write": true, "directory": "data/routes" }
```

## Non-goals

- Live UCI bus wiring inside this repo (o-my-sim owns publish)
- Binary / protobuf encoding (JSON first; schema id allows evolution)
