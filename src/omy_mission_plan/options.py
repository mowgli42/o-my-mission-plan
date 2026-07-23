"""Mission Options A/B/C — CONOPS iterative cycle (docs/CONOPS.md)."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .planning import PlanCycleResult, PlanningSession
from .suppliers import configured_supplier_id


EMPHASIS_EFFICIENT = "efficient"
EMPHASIS_SYNCHRONIZED = "synchronized"
EMPHASIS_UNEXPECTED_AXIS = "unexpected_axis"
VALID_EMPHASES = frozenset(
    {EMPHASIS_EFFICIENT, EMPHASIS_SYNCHRONIZED, EMPHASIS_UNEXPECTED_AXIS}
)
VALID_SLOTS = frozenset({"A", "B", "C"})
# Nominal cruise for timing indicators (not a physics model)
NOMINAL_CRUISE_KT = 420.0

DEFAULT_EMPHASIS_BY_SLOT = {
    "A": EMPHASIS_EFFICIENT,
    "B": EMPHASIS_SYNCHRONIZED,
    "C": EMPHASIS_UNEXPECTED_AXIS,
}

DEFAULT_AXIS_PROFILES: dict[str, list[str]] = {
    # Northern corridor then enter theater (published fixes only)
    "northern": ["MW-MUTLA", "KWI", "MW-BASRA"],
    # Southern / Gulf approach
    "southern": ["DHA", "BAH", "MW-KUWAIT-CITY"],
    # Western desert corridor
    "western": ["MW-WADI-AL-BATIN", "MW-MUTLA"],
}


def compute_sync_timing(
    result: PlanCycleResult,
    router_inputs: dict[str, Any],
    *,
    cruise_kt: float = NOMINAL_CRUISE_KT,
) -> dict[str, Any]:
    """
    Derive simple timing-alignment indicators for synchronized options.

    Not a multi-vehicle optimizer — advisory metrics from route geometry +
    saved BDA lag intent (docs/CONOPS.md).
    """
    bda_lag = float(router_inputs.get("bda_lag_minutes") or 30.0)
    sync_group = router_inputs.get("sync_group") or "wave-1"

    strike_tots: list[float] = []
    isr_etas: list[float] = []
    strike_platforms = 0
    isr_platforms = 0

    for plan in result.plans:
        if plan.status not in {"GO", "NO-GO"} or not plan.route:
            continue
        route = plan.route
        # Cumulative time to each waypoint
        times: list[float] = [0.0]
        for leg in route.legs:
            times.append(times[-1] + (leg.distance_nmi / cruise_kt) * 60.0)

        has_strike = False
        has_isr = False
        for i, wp in enumerate(route.waypoints):
            tid = wp.associated_task_id
            if not tid:
                continue
            # Infer type from task id prefix used in demo / insert
            if tid.startswith("STK") or "STRIKE" in tid.upper():
                has_strike = True
                if i < len(times):
                    strike_tots.append(times[i])
            elif tid.startswith("ISR"):
                has_isr = True
                if i < len(times):
                    isr_etas.append(times[i])
        # Fallback: aircraft type
        if plan.aircraft_type in {"FIGHTER", "BOMBER"} and plan.assigned_task_ids:
            if not has_strike and any(
                t.startswith("STK") for t in plan.assigned_task_ids
            ):
                has_strike = True
                # Use mid-route as crude TOT if association missing
                mid = len(times) // 2
                strike_tots.append(times[mid] if times else 0.0)
            strike_platforms += 1 if has_strike or plan.aircraft_type in {
                "FIGHTER",
                "BOMBER",
            } and any(t.startswith("STK") for t in plan.assigned_task_ids) else 0
        if plan.aircraft_type == "ISR" and plan.assigned_task_ids:
            isr_platforms += 1
            if not has_isr and times:
                isr_etas.append(times[-1] * 0.7)

    # Recount platforms cleanly
    strike_platforms = sum(
        1
        for p in result.plans
        if p.status in {"GO", "NO-GO"}
        and p.aircraft_type in {"FIGHTER", "BOMBER"}
        and any(t.startswith("STK") for t in (p.assigned_task_ids or []))
    )
    isr_platforms = sum(
        1
        for p in result.plans
        if p.status in {"GO", "NO-GO"}
        and p.aircraft_type == "ISR"
        and (p.assigned_task_ids or [])
    )

    tot_spread = (
        round(max(strike_tots) - min(strike_tots), 1) if len(strike_tots) >= 2 else 0.0
    )
    mean_tot = round(sum(strike_tots) / len(strike_tots), 1) if strike_tots else None
    # Alignment: good if strike TOTs cluster within 15 min
    if len(strike_tots) < 2:
        alignment = "single-platform" if strike_tots else "no-strike-tot"
        alignment_ok = True
    else:
        alignment_ok = tot_spread <= 15.0
        alignment = "aligned" if alignment_ok else "spread"

    bda_ok = None
    bda_slack_min = None
    if mean_tot is not None and isr_etas:
        # ISR should arrive at/after mean strike TOT + BDA lag
        earliest_isr = min(isr_etas)
        required = mean_tot + bda_lag
        bda_slack_min = round(earliest_isr - required, 1)
        bda_ok = earliest_isr >= required - 5.0  # 5 min tolerance

    return {
        "sync_group": sync_group,
        "bda_lag_minutes": bda_lag,
        "timing_alignment": alignment,
        "alignment_ok": alignment_ok,
        "tot_spread_minutes": tot_spread,
        "mean_strike_tot_minutes": mean_tot,
        "strike_platform_count": strike_platforms,
        "isr_platform_count": isr_platforms,
        "bda_lag_ok": bda_ok,
        "bda_slack_minutes": bda_slack_min,
        "cruise_kt_assumed": cruise_kt,
        "note": "Advisory indicators from geometry + lag intent; not a temporal optimizer.",
    }


class MissionOption(BaseModel):
    """Saved planning cycle with router inputs for compare / re-run."""

    option_id: str
    label: str
    emphasis: str
    slot: Optional[str] = None
    router_inputs: dict[str, Any] = Field(default_factory=dict)
    result: PlanCycleResult
    preferred: bool = False
    parent_option_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: list[str] = Field(default_factory=list)

    def summary_metrics(self) -> dict[str, Any]:
        s = self.result.summary
        total_distance = sum(
            (p.route.total_distance_nmi if p.route else 0.0) for p in self.result.plans
        )
        sync = None
        if self.emphasis == EMPHASIS_SYNCHRONIZED:
            sync = compute_sync_timing(self.result, self.router_inputs)
        return {
            "option_id": self.option_id,
            "label": self.label,
            "emphasis": self.emphasis,
            "slot": self.slot,
            "preferred": self.preferred,
            "parent_option_id": self.parent_option_id,
            "go_count": s.get("go", 0),
            "nogo_count": s.get("nogo", 0),
            "unallocated_count": s.get("unallocated", 0),
            "idle_count": s.get("idle", 0),
            "total_distance_nmi": round(total_distance, 2),
            "supplier_id": self.router_inputs.get("supplier_id"),
            "vias": list(self.router_inputs.get("vias") or []),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": list(self.notes),
            "sync": sync,
        }

    def to_list_item(self) -> dict[str, Any]:
        item = self.summary_metrics()
        item["router_inputs"] = deepcopy(self.router_inputs)
        return item

    def to_detail(self) -> dict[str, Any]:
        item = self.to_list_item()
        item["result"] = self.result.model_dump(mode="json")
        return item


class OptionStore:
    def __init__(self) -> None:
        self._options: dict[str, MissionOption] = {}
        self._slots: dict[str, str] = {}

    def clear(self) -> None:
        self._options.clear()
        self._slots.clear()

    def get(self, option_id: str) -> Optional[MissionOption]:
        return self._options.get(option_id)

    def list_options(self) -> list[MissionOption]:
        return sorted(self._options.values(), key=lambda o: o.created_at)

    def slot_map(self) -> dict[str, Optional[str]]:
        return {s: self._slots.get(s) for s in ("A", "B", "C")}

    def add(self, option: MissionOption) -> MissionOption:
        self._options[option.option_id] = option
        if option.slot:
            self.assign_slot(option.option_id, option.slot)
        return option

    def assign_slot(self, option_id: str, slot: str) -> MissionOption:
        if slot not in VALID_SLOTS:
            raise ValueError(f"slot must be one of {sorted(VALID_SLOTS)}")
        opt = self._options.get(option_id)
        if opt is None:
            raise KeyError(option_id)
        prev = self._slots.get(slot)
        if prev and prev in self._options and prev != option_id:
            self._options[prev].slot = None
        if opt.slot and self._slots.get(opt.slot) == option_id:
            del self._slots[opt.slot]
        opt.slot = slot
        opt.updated_at = datetime.now(timezone.utc)
        self._slots[slot] = option_id
        return opt

    def set_preferred(self, option_id: str) -> MissionOption:
        opt = self._options.get(option_id)
        if opt is None:
            raise KeyError(option_id)
        for other in self._options.values():
            other.preferred = other.option_id == option_id
        opt.updated_at = datetime.now(timezone.utc)
        return opt

    def get_preferred(self) -> Optional[MissionOption]:
        for opt in self._options.values():
            if opt.preferred:
                return opt
        return None


OPTION_STORE = OptionStore()


def axis_vias(axis_name: str, profiles: Optional[dict[str, list[str]]] = None) -> list[str]:
    profiles = profiles or DEFAULT_AXIS_PROFILES
    if axis_name not in profiles:
        raise KeyError(f"Unknown axis profile: {axis_name}")
    return list(profiles[axis_name])


def build_router_inputs(
    emphasis: str,
    *,
    supplier_id: Optional[str] = None,
    vias: Optional[list[str]] = None,
    avoid_fix_ids: Optional[list[str]] = None,
    axis_name: Optional[str] = None,
    sync_group: str = "wave-1",
    bda_lag_minutes: float = 30.0,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    if emphasis not in VALID_EMPHASES:
        raise ValueError(f"emphasis must be one of {sorted(VALID_EMPHASES)}")
    sid = supplier_id or configured_supplier_id()
    inputs: dict[str, Any] = {
        "emphasis": emphasis,
        "supplier_id": sid,
        "vias": list(vias or []),
        "avoid_fix_ids": list(avoid_fix_ids or []),
    }
    if emphasis == EMPHASIS_EFFICIENT:
        inputs["vias"] = []
        inputs.pop("axis_name", None)
        inputs.pop("sync_group", None)
        inputs.pop("bda_lag_minutes", None)
        inputs.pop("timing_alignment", None)
    elif emphasis == EMPHASIS_SYNCHRONIZED:
        inputs["vias"] = list(vias or [])
        inputs["sync_group"] = sync_group
        inputs["bda_lag_minutes"] = bda_lag_minutes
        inputs["timing_alignment"] = "intent-recorded"
        inputs.pop("axis_name", None)
    else:
        name = axis_name or "northern"
        forced = list(vias) if vias is not None else axis_vias(name)
        inputs["vias"] = forced
        inputs["axis_name"] = name
        inputs["axis_profile"] = name
        inputs.pop("sync_group", None)
        inputs.pop("bda_lag_minutes", None)
        inputs.pop("timing_alignment", None)
    if extra:
        # Extra must not silently invent PROX geometry; only metadata / overrides
        for k, v in extra.items():
            if k in {"emphasis"}:
                continue
            inputs[k] = v
        # Re-assert emphasis geometry rules after merge for efficient
        if emphasis == EMPHASIS_EFFICIENT and "vias" not in (extra or {}):
            inputs["vias"] = []
    return inputs


def create_option_from_session(
    planning: PlanningSession,
    *,
    label: str,
    emphasis: str,
    slot: Optional[str] = None,
    supplier_id: Optional[str] = None,
    vias: Optional[list[str]] = None,
    avoid_fix_ids: Optional[list[str]] = None,
    axis_name: Optional[str] = None,
    sync_group: str = "wave-1",
    bda_lag_minutes: float = 30.0,
    parent_option_id: Optional[str] = None,
    router_input_overrides: Optional[dict[str, Any]] = None,
    store: Optional[OptionStore] = None,
) -> MissionOption:
    """Apply router inputs, run plan cycle, persist Mission Option."""
    store = store or OPTION_STORE
    inputs = build_router_inputs(
        emphasis,
        supplier_id=supplier_id,
        vias=vias,
        avoid_fix_ids=avoid_fix_ids,
        axis_name=axis_name,
        sync_group=sync_group,
        bda_lag_minutes=bda_lag_minutes,
        extra=router_input_overrides,
    )
    planning.apply_router_inputs(inputs)
    result = planning.run_plan_cycle()
    notes: list[str] = list(planning.last_supplier_notes)
    if emphasis == EMPHASIS_SYNCHRONIZED:
        notes.append(
            f"Synchronized: sync_group={inputs.get('sync_group')}, "
            f"bda_lag_minutes={inputs.get('bda_lag_minutes')} "
            "(timing metadata; lateral path uses supplier + published fixes)."
        )
    if emphasis == EMPHASIS_UNEXPECTED_AXIS:
        notes.append(
            f"Unexpected-axis: axis={inputs.get('axis_name')} vias={inputs.get('vias')}"
        )

    option = MissionOption(
        option_id=str(uuid4()),
        label=label,
        emphasis=emphasis,
        slot=None,
        router_inputs=inputs,
        result=result,
        parent_option_id=parent_option_id,
        notes=notes,
    )
    store.add(option)
    if slot:
        store.assign_slot(option.option_id, slot)
    return option


def ensure_top_three(
    planning: PlanningSession,
    *,
    store: Optional[OptionStore] = None,
    force: bool = False,
    supplier_id: Optional[str] = None,
) -> list[MissionOption]:
    store = store or OPTION_STORE
    labels = {
        "A": "Option A — Efficient",
        "B": "Option B — Synchronized",
        "C": "Option C — Unexpected axis",
    }
    if force:
        # Replace working set cleanly for demo / showcase rebuilds
        store.clear()
    created: list[MissionOption] = []
    for slot, emphasis in DEFAULT_EMPHASIS_BY_SLOT.items():
        existing_id = store.slot_map().get(slot)
        if existing_id and not force:
            continue
        opt = create_option_from_session(
            planning,
            label=labels[slot],
            emphasis=emphasis,
            slot=slot,
            supplier_id=supplier_id,
            axis_name="northern" if emphasis == EMPHASIS_UNEXPECTED_AXIS else None,
            store=store,
        )
        created.append(opt)
    return created


def rerun_option(
    planning: PlanningSession,
    option_id: str,
    *,
    router_input_overrides: Optional[dict[str, Any]] = None,
    as_new: bool = True,
    label: Optional[str] = None,
    store: Optional[OptionStore] = None,
) -> MissionOption:
    """
    Re-run with saved inputs (+ optional patches).

    By default creates a new option linked to the parent (CONOPS iterate).
    Set as_new=False to replace the existing option's result in place.
    """
    store = store or OPTION_STORE
    parent = store.get(option_id)
    if parent is None:
        raise KeyError(option_id)

    inputs = deepcopy(parent.router_inputs)
    if router_input_overrides:
        inputs.update(router_input_overrides)
    emphasis = str(inputs.get("emphasis") or parent.emphasis)
    if emphasis not in VALID_EMPHASES:
        raise ValueError(f"emphasis must be one of {sorted(VALID_EMPHASES)}")
    inputs = build_router_inputs(
        emphasis,
        supplier_id=inputs.get("supplier_id"),
        vias=inputs.get("vias"),
        avoid_fix_ids=inputs.get("avoid_fix_ids"),
        axis_name=inputs.get("axis_name"),
        sync_group=str(inputs.get("sync_group") or "wave-1"),
        bda_lag_minutes=float(inputs.get("bda_lag_minutes") or 30.0),
        extra={k: v for k, v in inputs.items() if k not in {
            "emphasis", "supplier_id", "vias", "avoid_fix_ids",
            "axis_name", "sync_group", "bda_lag_minutes",
        }},
    )

    planning.apply_router_inputs(inputs)
    result = planning.run_plan_cycle()
    notes = list(planning.last_supplier_notes) + ["Re-run with saved/updated router inputs"]

    if as_new:
        child = MissionOption(
            option_id=str(uuid4()),
            label=label or f"{parent.label} (rerun)",
            emphasis=emphasis,
            slot=None,
            router_inputs=inputs,
            result=result,
            parent_option_id=parent.option_id,
            notes=notes,
        )
        return store.add(child)

    parent.router_inputs = inputs
    parent.emphasis = emphasis
    parent.result = result
    parent.notes.extend(notes)
    parent.updated_at = datetime.now(timezone.utc)
    return parent


def resolve_export_option_id(
    option_id: Optional[str] = None,
    *,
    store: Optional[OptionStore] = None,
) -> tuple[Optional[str], Optional[PlanCycleResult]]:
    """Pick explicit option_id, else preferred option, else None (use session latest)."""
    store = store or OPTION_STORE
    if option_id:
        opt = store.get(option_id)
        if opt is None:
            raise KeyError(option_id)
        return opt.option_id, opt.result
    preferred = store.get_preferred()
    if preferred is not None:
        return preferred.option_id, preferred.result
    return None, None


def compare_options(
    option_ids: Optional[list[str]] = None,
    *,
    store: Optional[OptionStore] = None,
) -> dict[str, Any]:
    store = store or OPTION_STORE
    if option_ids:
        opts = []
        for oid in option_ids:
            opt = store.get(oid)
            if opt is None:
                raise KeyError(oid)
            opts.append(opt)
    else:
        slotted = []
        for slot in ("A", "B", "C"):
            oid = store.slot_map().get(slot)
            if oid:
                opt = store.get(oid)
                if opt:
                    slotted.append(opt)
        opts = slotted or store.list_options()

    preferred = store.get_preferred()
    return {
        "human_in_the_loop": True,
        "note": (
            "Comparison is advisory; planner selects preferred option for "
            "export. No automatic best-option picker."
        ),
        "slots": store.slot_map(),
        "preferred_option_id": preferred.option_id if preferred else None,
        "options": [o.summary_metrics() for o in opts],
    }
