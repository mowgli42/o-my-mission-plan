"""Force engagement archetypes + GapReport stubs (docs/FORCE-APPROACHES.md)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from .planning import PlanCycleResult


# Canonical archetype ids from FORCE-APPROACHES §2
ARCHETYPE_EFFICIENT = "efficient"
ARCHETYPE_SYNCHRONIZED = "synchronized"
ARCHETYPE_MANEUVER = "maneuver"
ARCHETYPE_SURPRISE = "surprise"
ARCHETYPE_SHOCK = "shock"
ARCHETYPE_ATTRITION = "attrition"

VALID_ARCHETYPES = frozenset(
    {
        ARCHETYPE_EFFICIENT,
        ARCHETYPE_SYNCHRONIZED,
        ARCHETYPE_MANEUVER,
        ARCHETYPE_SURPRISE,
        ARCHETYPE_SHOCK,
        ARCHETYPE_ATTRITION,
    }
)

# Map legacy CONOPS emphasis → primary archetype
EMPHASIS_TO_ARCHETYPE = {
    "efficient": ARCHETYPE_EFFICIENT,
    "synchronized": ARCHETYPE_SYNCHRONIZED,
    "unexpected_axis": ARCHETYPE_MANEUVER,
}

ARCHETYPE_TO_EMPHASIS = {
    ARCHETYPE_EFFICIENT: "efficient",
    ARCHETYPE_SYNCHRONIZED: "synchronized",
    ARCHETYPE_MANEUVER: "unexpected_axis",
    ARCHETYPE_SURPRISE: "unexpected_axis",
    ARCHETYPE_SHOCK: "efficient",
    ARCHETYPE_ATTRITION: "efficient",
}

ARCHETYPE_CATALOG: list[dict[str, Any]] = [
    {
        "id": ARCHETYPE_EFFICIENT,
        "label": "Efficient / economy of force",
        "aim": "Cover tasks with least fuel/time/risk to own force",
    },
    {
        "id": ARCHETYPE_SYNCHRONIZED,
        "label": "Synchronized effects",
        "aim": "Time-align collection, strike, BDA, mutual support",
    },
    {
        "id": ARCHETYPE_MANEUVER,
        "label": "Maneuver / indirect",
        "aim": "Dislocate; fight where the enemy is weak or unready",
    },
    {
        "id": ARCHETYPE_SURPRISE,
        "label": "Surprise",
        "aim": "Achieve effects before the enemy can adapt",
    },
    {
        "id": ARCHETYPE_SHOCK,
        "label": "Shock / rapid dominance",
        "aim": "Overwhelm C2 and will in a short window",
    },
    {
        "id": ARCHETYPE_ATTRITION,
        "label": "Attrition / resilience",
        "aim": "Absorb cost; remain coherent; deny enemy decision",
    },
]


class GapItem(BaseModel):
    code: str
    severity: str = "MEDIUM"  # LOW | MEDIUM | HIGH | CRITICAL
    narrative: str
    related_task_ids: list[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    code: str
    likelihood: str = "MEDIUM"
    impact: str = "MEDIUM"
    mitigation_hint: str = ""


class DependencyItem(BaseModel):
    frm: str = Field(alias="from")
    to: str
    kind: str = "timing"  # timing | platform | corridor

    model_config = {"populate_by_name": True}


class GapReport(BaseModel):
    """Rules-only stub for later AI assessment (FORCE-APPROACHES §5)."""

    option_id: str
    archetype: str
    gaps: list[GapItem] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)
    dependencies: list[DependencyItem] = Field(default_factory=list)
    missing_contingency_hints: list[str] = Field(default_factory=list)
    human_in_the_loop: bool = True
    note: str = (
        "Advisory rules stub — does not pick a best option. "
        "See docs/FORCE-APPROACHES.md §5."
    )


def resolve_archetype(
    *,
    archetype: Optional[str] = None,
    emphasis: Optional[str] = None,
    hybrid_tags: Optional[list[str]] = None,
) -> tuple[str, list[str]]:
    """Return (primary_archetype, hybrid_tags)."""
    tags = [t for t in (hybrid_tags or []) if t in VALID_ARCHETYPES]
    if archetype and archetype in VALID_ARCHETYPES:
        primary = archetype
    elif emphasis and emphasis in EMPHASIS_TO_ARCHETYPE:
        primary = EMPHASIS_TO_ARCHETYPE[emphasis]
    else:
        primary = ARCHETYPE_EFFICIENT
    if primary == ARCHETYPE_MANEUVER and ARCHETYPE_SURPRISE not in tags:
        # Default C-style hybrid hint
        if emphasis == "unexpected_axis":
            tags = list(dict.fromkeys([*tags, ARCHETYPE_SURPRISE]))
    return primary, tags


def archetype_fit_hint(
    archetype: str,
    *,
    vias: list[str],
    sync: Optional[dict[str, Any]],
    total_distance_nmi: float,
    baseline_distance_nmi: Optional[float] = None,
) -> str:
    if archetype == ARCHETYPE_EFFICIENT:
        if vias:
            return "fit-warn: efficient option still has forced vias"
        return "fit-ok: short-path bias, no forced vias"
    if archetype == ARCHETYPE_SYNCHRONIZED:
        if not sync:
            return "fit-warn: synchronized without timing indicators"
        if sync.get("alignment_ok"):
            return "fit-ok: timing indicators present"
        return "fit-warn: desync risk on TOT / BDA"
    if archetype in {ARCHETYPE_MANEUVER, ARCHETYPE_SURPRISE}:
        if not vias:
            return "fit-warn: maneuver/surprise without forced vias"
        if baseline_distance_nmi and total_distance_nmi <= baseline_distance_nmi * 1.02:
            return "fit-warn: geometry still looks like efficient baseline"
        return "fit-ok: non-obvious via corridor vs direct"
    if archetype == ARCHETYPE_SHOCK:
        return "fit-info: shock — check early-task GO + assessment branch"
    if archetype == ARCHETYPE_ATTRITION:
        return "fit-info: attrition — check redundancy / fuel margin"
    return "fit-info"


def build_gap_report(
    option_id: str,
    archetype: str,
    result: PlanCycleResult,
    *,
    vias: Optional[list[str]] = None,
    sync: Optional[dict[str, Any]] = None,
    hybrid_tags: Optional[list[str]] = None,
    pool_archetypes: Optional[list[str]] = None,
) -> GapReport:
    """Rules-only GapReport from FORCE-APPROACHES checklist."""
    gaps: list[GapItem] = []
    risks: list[RiskItem] = []
    deps: list[DependencyItem] = []
    hints: list[str] = []

    unalloc = list(result.allocation.unallocated_task_ids)
    if unalloc:
        gaps.append(
            GapItem(
                code="coverage.unallocated",
                severity="HIGH",
                narrative=f"{len(unalloc)} task(s) remain unallocated",
                related_task_ids=unalloc[:12],
            )
        )

    nogo = [p for p in result.plans if p.status == "NO-GO"]
    if nogo:
        gaps.append(
            GapItem(
                code="feasibility.nogo",
                severity="CRITICAL",
                narrative=f"{len(nogo)} aircraft NO-GO on fuel reserves",
                related_task_ids=[],
            )
        )

    unsat = []
    for p in result.plans:
        unsat.extend(p.unsatisfied_task_ids or [])
    if unsat:
        gaps.append(
            GapItem(
                code="coverage.proximity",
                severity="HIGH",
                narrative="Assigned tasks lack published-fix proximity",
                related_task_ids=list(dict.fromkeys(unsat))[:12],
            )
        )

    # Single-platform concentration
    strike_owners = [
        p.aircraft_id
        for p in result.plans
        if any(t.startswith("STK") for t in (p.assigned_task_ids or []))
    ]
    if len(strike_owners) == 1:
        risks.append(
            RiskItem(
                code="spf.strike_platform",
                likelihood="MEDIUM",
                impact="HIGH",
                mitigation_hint="Spread strikes or add contingency attrition option",
            )
        )

    vias = list(vias or [])
    if archetype in {ARCHETYPE_MANEUVER, ARCHETYPE_SURPRISE} and not vias:
        gaps.append(
            GapItem(
                code="archetype.fit",
                severity="MEDIUM",
                narrative="Maneuver/surprise archetype lacks forced published vias",
            )
        )

    if archetype == ARCHETYPE_SYNCHRONIZED:
        if sync and sync.get("bda_lag_ok") is False:
            gaps.append(
                GapItem(
                    code="sync.bda_lag",
                    severity="HIGH",
                    narrative="ISR may arrive before BDA lag window vs mean strike TOT",
                )
            )
        if sync and not sync.get("alignment_ok", True):
            gaps.append(
                GapItem(
                    code="sync.tot_spread",
                    severity="MEDIUM",
                    narrative=f"Strike TOT spread {sync.get('tot_spread_minutes')} min exceeds alignment band",
                )
            )
        deps.append(
            DependencyItem(
                **{"from": "strike-wave", "to": "isr-bda", "kind": "timing"}
            )
        )

    pool = set(pool_archetypes or [])
    if ARCHETYPE_ATTRITION not in pool and archetype != ARCHETYPE_ATTRITION:
        hints.append(
            "Consider an attrition/resilience contingency if the primary axis is denied"
        )
    if archetype == ARCHETYPE_MANEUVER and ARCHETYPE_EFFICIENT not in pool:
        hints.append("Keep an efficient baseline pinned for comparison against maneuver")

    return GapReport(
        option_id=option_id,
        archetype=archetype,
        gaps=gaps,
        risks=risks,
        dependencies=deps,
        missing_contingency_hints=hints,
    )
