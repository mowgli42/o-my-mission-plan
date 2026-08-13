# Tasks — add-route-planner-modes

## Validated prototype slice (graham-bell)

- [ ] Document modes + algorithms (`docs/ROUTE-PLANNER-MODES.md`) — done
- [ ] API contract (`docs/API-PROTOTYPE-SERVICES.md`) — done
- [ ] Extend Task with optional window + target_id; Target model; PlatformCapacity
- [ ] `POST /api/allocate` with coa_bias + time windows + capacity
- [ ] `POST /api/route/plan` with mode enum (efficient, threat_avoid, spread_field, area_loiter, unexpected_axis, synchronized)
- [ ] `threat_avoid` uses existing costgrid penalties + exposure_score
- [ ] `area_loiter` simple cyclic published fixes + loiter_minutes fuel debit
- [ ] `spread_field` advisory separation notes or light peer-edge penalty (document honesty)
- [ ] `POST /api/iterate` full cycle → Mission Option
- [ ] Unit tests: platform count differs by bias; threat path bends; loiter metric present
- [ ] Gherkin: Validated scenarios for above; Future for RRT/MAPF/MILP
- [ ] Beads roadmap for production rebuild

## Future / beads only

- [ ] X-Plane denser graph interaction with modes
- [ ] True MAPF spread_field
- [ ] Optimal time-window mTSP allocation
