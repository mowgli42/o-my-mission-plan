# openRouteFinder spike — PSAB published nav graph

## Goal (issue #6)

Prove the **supplier adapter** shape against the Gulf War / PSAB demo without
taking a hard dependency on the upstream openRouteFinder package.

## What shipped

| Piece | Role |
|-------|------|
| `suppliers/graph_routing.py` | Pure-Python Dijkstra over published fixes (k-nearest links ≤ 500 nmi) |
| `suppliers/openroutefinder.py` | ORF-style supplier: graph path origin → vias → task covers → home |
| `ROUTE_SUPPLIER=openroutefinder` | Selects the spike adapter |

When the optional `openroutefinder` package is importable, the adapter records a
note and still uses the in-repo PSAB graph (upstream graph formats differ from
our published-fix set). Fallback remains available if the graph path fails.

## How to try

```bash
ROUTE_SUPPLIER=openroutefinder make demo
# or in the Options tab, pick openroutefinder → Build A / B / C
```

Compare notes on planned aircraft (`supplier_source` / option notes): you should
see graph hop counts and ORF-style messaging — still **published waypoints only**.

## Findings

1. **Published-only constraint fits Dijkstra well** — nodes are airbases, navaids,
   and fixed mission waypoints; no PROX inventing.
2. **Task coverage** — ORF-style paths insert covering fixes (same 80/20 nmi
   radii) as intermediate vias so proximity association still succeeds.
3. **Upstream package** — not required for the prototype; treat real airway DB
   coupling as a later theater-navdata ticket.
4. **Cost-grid (#7)** reuses the same graph with avoid-zone edge penalties.

## Non-goals

- Full ARINC 424 / Little Navmap import
- Calling a remote ORF HTTP service from CI
- Replacing the fuel propagator
