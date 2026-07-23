"""Constant-burn fuel propagation and GO / NO-GO feasibility."""

from __future__ import annotations

from .models import Aircraft, FuelState, Route


def propagate(route: Route, aircraft: Aircraft) -> tuple[Route, FuelState]:
    """
    Fill per-leg fuel burn / remaining and set overall feasibility.

    Feasible (GO) iff final fuel ≥ reserve_fuel.
    """
    remaining = aircraft.initial_fuel
    after: list[float] = []

    for leg in route.legs:
        burn = leg.distance_nmi * aircraft.burn_rate_per_nmi
        remaining = remaining - burn
        leg.fuel_burn = round(burn, 2)
        leg.fuel_remaining_after = round(remaining, 2)
        after.append(leg.fuel_remaining_after)

    final = remaining
    feasible = final >= aircraft.reserve_fuel
    reason = None
    if not feasible:
        reason = (
            f"Unexecutable due to fuel: end fuel {final:.1f} "
            f"< reserve {aircraft.reserve_fuel:.1f}"
        )

    route.feasible = feasible
    route.infeasible_reason = reason

    state = FuelState(
        aircraft_id=aircraft.id,
        initial_fuel=aircraft.initial_fuel,
        reserve_fuel=aircraft.reserve_fuel,
        burn_rate_per_nmi=aircraft.burn_rate_per_nmi,
        remaining_after_legs=after,
        final_fuel=round(final, 2),
        feasible=feasible,
        infeasible_reason=reason,
    )
    return route, state
