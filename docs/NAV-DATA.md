# Navigation data — fixtures vs X-Plane extract

## Intent

Routes use **published waypoints only**. The demo can load a denser theater
navaid set from an X-Plane–style `earth_nav.dat` extract without requiring FAA
CIFP or commercial navdata.

## Config

| Env | Values | Default |
|-----|--------|---------|
| `NAV_SOURCE` | `fixture` \| `xplane` | `fixture` |
| `XPLANE_NAV_PATH` | path to `earth_nav.dat` extract | `data/nav/gulf-earth_nav.dat` |

```bash
NAV_SOURCE=xplane make demo
```

Without the extract file, the loader falls back to hard-coded fixtures in
`demo_world.py` so the prototype always runs.

## Shipped extract

`data/nav/gulf-earth_nav.dat` is a **small, demo-scale** Gulf/PSAB theater
file (~30 fixes) in X-Plane row layout (`type lat lon … ident name`).

**Attribution / license notes for the demo:**

- Coordinates are **synthetic demo positions** inspired by publicly charted
  regional fixes — **not** a redistributed X-Plane global database dump.
- Do **not** commit full worldwide `earth_nav.dat` binaries to git.
- To use a real X-Plane cycle extract: filter to the Gulf bbox offline, drop
  the file at `data/nav/gulf-earth_nav.dat` (or set `XPLANE_NAV_PATH`), and
  keep Laminar Research / X-Plane license terms if redistributing their data.

## Loader behavior

1. Always keep fixture **airbases** + **mission waypoints**.
2. Start from fixture **navaids**.
3. If `NAV_SOURCE=xplane` and the file exists, parse types `2` (VOR), `3` (NDB),
   `13` (DME) inside the theater bbox and merge (extract overlays same ids).
4. `build_default_graph` / plan cycle use the merged published set.
5. World snapshot reports `nav_source`, `navaid_count`, and notes.

## Related

- `docs/WAYPOINT-AND-ROUTING-MODEL.md` — unified waypoint representation
- `docs/ROUTE-GENERATION.md` — no `PROX-*` inventing
- Issue #14
