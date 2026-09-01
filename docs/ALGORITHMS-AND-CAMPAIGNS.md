# Algorithms and Campaigns — Tactician Read-Across

Companion to [`FORCE-APPROACHES.md`](FORCE-APPROACHES.md) and [`ROUTING-ALGORITHMS-WALKTHROUGH.md`](ROUTING-ALGORITHMS-WALKTHROUGH.md).

A route solver is not a commander. Dijkstra will send every fighter down the same cheap corridor. VRP will fill the last weapon slot because the truck was not full. The tactician chooses **which objective the math may minimize** — fuel, time, exposure, surprise, or redundancy — and keeps a second option when the first assumption dies.

Teaching analogues only. Not templates to copy onto a new theater.

---

## Staff work the algorithms already describe

| Staff question | Pre-computer practice | Named algorithm |
|----------------|----------------------|-----------------|
| What can arrive by H-hour? | March tables, tidal graphs, railway grafikon | Isochrones |
| Which road avoids the guns? | Corridor briefs, flak maps, SEAD packages | Dijkstra / A* on a cost field |
| Who takes which objective, with what load? | ATO frag, march serials, tanker tracks | VRP / mTSP / covering salesman |

The ATO *is* a VRP with time windows. The IADS picture *is* a cost field. “Can the left hook still close by G+2?” *is* an isochrone.

## Math, short

| Year | Result | Planner interest |
|------|--------|------------------|
| Dijkstra 1956 | Shortest path, non-negative weights | Civil hop; any O-D cost |
| Dantzig & Ramser 1959 (RAND) | Truck dispatching / VRP | Fleet + capacity = ATO skeleton |
| Clarke & Wright 1964 | Savings heuristic | Still a construct step |
| Hart, Nilsson, Raphael 1968 | A* | Goal-directed search on a painted map |
| James / Hagiwara | Ship isochrones | Time fronts; TOT slack |
| Late Cold War OR | Aircraft CSP under SAM risk | Mission-area hop |

---

## COA → tactic → campaign → algorithm

| If the commander says | History in his head | Run this math |
|-----------------------|---------------------|---------------|
| Don't waste jets | Economy of force | CVRP pack + short Dijkstra |
| Hit together, then look | Normandy; kill-chain; AirLand | VRPTW + precedence; isochrone slack |
| They are watching the causeway | Left hook 1991; Inchon 1950; Ardennes 1940 | Forced western vias |
| I will not fly that umbrella | Route packages; SEAD-first | A* on threat field |
| One missile must not kill the package | Dispersed ops | mTSP; raise platforms_used |
| Stay overhead after the pass | CAP / AWACS / Battle of Britain standing patrols | Loiter cycle + burn |
| If the west is closed | Residual force; Kursk defensive lesson | Attrition contingency |

### Grain on the campaigns

- **1940 Ardennes** — Allies painted the forest as infinite cost and ran the efficient northern hop. Army Group A paid traffic and fuel for dislocation. Pair with COA A vs C.
- **Inchon 1950** — cheap hop was another punch at Pusan; the costed path used a tide-bound port. Surprise was perishable (isochrone + unexpected axis).
- **Normandy 1944** — tide, drop, guns, infantry as one chord. Desync is the failure mode. COA B.
- **Red Ball Express / Berlin Airlift** — VRP under capacity and a thin graph. One cheap edge becomes a traffic jam; many airframes + published corridors + windows is VRPTW.
- **Bomber Command 1943 vs later** — same target graph; adding escort, night, and EW changed the *paint*, not the itinerary type. Schweinfurt is what happens when threat cost is under-weighted.
- **Desert Storm** — dummy cost field opposite Kuwait; real A* through the west; air campaign as synchronization *before* the hook.
- **Suez 1973** — unexpected axis that still arrived inside the enemy decision cycle. A slow western via is just a scenic efficient route.

---

## Inspection (tactician, not solver)

- If A looks like the enemy principal engagement area, you have built his fire plan.
- If B has no named TOT and no named collector, you have two unrelated sorties.
- If C arrives after surprise would have decayed, you bought extra stamps.
- If no option survives one lost airframe or corridor, the pool needs an attrition branch.
- If A/B/C are clones on `platforms_used` and axis, comparison is theater.
- If any option is NO-GO on reserve fuel, the tactic is a briefing slide.

Algorithms assume the cost field is known. Most operational disasters were **bad fields**, not bad shortest-path code.
