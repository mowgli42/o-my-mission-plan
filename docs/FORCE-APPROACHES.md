# Force Engagement Approaches — Historical Analysis & Planning Archetypes

## Purpose

The mission planner does not only vary **geometry** (short path vs unexpected axis). It varies **operational approach**: what the force is trying to achieve and what risks it is willing to accept.

This document:

1. Reviews historical battles where distinct approaches dominated
2. Derives planning **archetypes** the tool can label and store
3. States **objectives and guidelines** for each archetype (what “good” means)
4. Defines how the **top-three working set** and additional **contingencies** relate
5. Sets the evaluation criteria later AI gap/risk/dependency assessment should use

The current UI slots A/B/C remain the *default visible trio*. The system may store more named contingencies; A/B/C are the ones held in continuous comparison.

---

## 1. Historical patterns (selected cases)

### Maneuver / indirect approach

| Case | What happened | Operational idea |
|------|----------------|------------------|
| **France 1940 (Ardennes)** | Main effort through terrain assessed as unsuitable for armor; Allied expectation fixed on a northern thrust | Avoid the enemy’s strength; collapse decision cycle by appearing where not expected |
| **Inchon 1950** | Amphibious landing far behind NKPA lines instead of another frontal push at the Pusan perimeter | Operational discontinuity — strike the rear and lines of communication |
| **Desert Storm 1991 “Left Hook”** | After a visible buildup opposite Kuwait, VII Corps swung west through the desert to envelop Iraqi forces | Fix attention on the obvious axis; decisive maneuver on the open flank |
| **Six-Day War 1967 (air + ground)** | Preemptive destruction of Arab air forces, then rapid multi-axis ground advances | Seize initiative; shatter enemy coherence before attrition sets in |

**Common traits:** tempo, dislocation, preference for the enemy’s weakness or unprepared axis, acceptance of logistics and C2 stretch in exchange for decision advantage.

### Attrition / resilience

| Case | What happened | Operational idea |
|------|----------------|------------------|
| **Western Front 1916–18** | Material and manpower applied until the opponent’s system broke | Win by cumulative destruction and superior replacement |
| **Stalingrad 1942–43 (Soviet)** | Absorb, hold urban terrain, then counter-encircle | Trade space/time; preserve a coherent force that can still strike |
| **Kursk 1943 (defensive phase)** | Deep prepared defenses bled German armor before counteroffensive | Force the enemy to attack into strength; conserve own offensive power |

**Common traits:** depth, redundancy, acceptance of higher cost in exchange for robustness; success measured in remaining combat power and denied enemy objectives—not in elegant geometry.

### Surprise

| Case | What happened | Operational idea |
|------|----------------|------------------|
| **Pearl Harbor 1941** | Carrier strike at a base believed secure | Strategic/operational surprise against a fixed posture |
| **Yom Kippur 1973 (Suez crossing)** | Attack on a holiday along a line Israel considered defensible with minimal force | Tactical–operational surprise to seize a corridor before reserves arrive |
| **Operation Focus 1967** | Massed air attack on grounded aircraft | Compress the enemy’s ability to respond in the opening hours |

**Common traits:** deception, timing, intelligence advantage; high payoff if surprise holds, high penalty if it fails and the force is committed on a thin plan.

### Shock / rapid dominance

| Case | What happened | Operational idea |
|------|----------------|------------------|
| **Desert Storm air campaign** | Sustained, systematic degradation of C2, air defenses, and fielded forces before ground maneuver | Overwhelm systems so ground combat is short and one-sided |
| **Opening of OIF 2003 (“shock and awe” framing)** | Rapid advance on the capital with heavy joint fires | Psychological and physical paralysis of regime control |
| **Early Barbarossa 1941** | Simultaneous multi-axis penetration and encirclements | Collapse frontier armies before strategic depth can organize |

**Common traits:** massed effects in time, joint integration, aim to break will or coherence quickly; depends on accurate targeting and sustained tempo.

### Synchronized / combined effects

| Case | What happened | Operational idea |
|------|----------------|------------------|
| **Normandy 1944** | Air, sea, airborne, and land timed to open and hold a lodgment | Multi-domain timing so no single arm fights alone |
| **AirLand Battle concepts (late Cold War)** | Deep attack + close fight as one operational design | Effects in depth timed with the close battle |
| **Modern kill-chain exercises** | Sensor → decide → shooter compressed and rehearsed | Collection, strike, and BDA as one loop, not sequential afterthoughts |

**Common traits:** explicit timing relationships (TOT, BDA lag, mutual support); failure mode is desynchronization—arms arriving in the wrong order.

---

## 2. Planning archetypes for the tool

Map history to **named approaches** the planner can assign to any Mission Option (including the default A/B/C slots).

| Archetype ID | Label | Historical anchors | Primary aim |
|--------------|-------|--------------------|-------------|
| `maneuver` | Maneuver / indirect | Ardennes 1940, Inchon, Left Hook | Dislocate; fight where the enemy is weak or unready |
| `attrition` | Attrition / resilience | Kursk defensive, protracted material fights | Absorb cost; remain coherent; deny enemy decision |
| `surprise` | Surprise | Focus 1967, Yom Kippur crossing | Achieve effects before the enemy can adapt |
| `shock` | Shock / rapid dominance | Desert Storm air, early deep penetrations | Overwhelm C2 and will in a short window |
| `synchronized` | Synchronized effects | Normandy, AirLand, kill-chain | Time-align collection, strike, BDA, mutual support |
| `efficient` | Efficient / economy of force | Logistics-constrained raids, minimal-path packages | Cover tasks with least fuel/time/risk to own force |

**Default slot mapping (prototype):**

| Slot | Default archetype | Route bias (from existing CONOPS) |
|------|-------------------|-----------------------------------|
| **A** | `efficient` (optionally hybrid with light maneuver) | Short published-waypoint paths |
| **B** | `synchronized` | Shared holds/IPs, TOT windows, BDA-after-strike |
| **C** | `maneuver` + `surprise` (unexpected axis) | Forced vias / non-obvious corridor |

Additional contingencies may use `shock`, pure `attrition`, or explicit hybrids. The tool stores **many** options; **three** stay pinned for continuous comparison.

---

## 3. Objectives and guidelines per archetype

These are the **success criteria** and **risk postures** a human or later AI evaluator should use. They are intentionally normative for planning quality—not moral judgments about war.

### A / `efficient` — Economy of force

**Objective:** Accomplish assigned collection and strike tasks with minimum aggregate fuel, time, and exposure consistent with GO fuel reserves.

**Guidelines:**
- Prefer published waypoints and short great-circle sequences
- Minimize unallocated critical tasks before optimizing distance
- Do not accept NO-GO fuel states to shave distance
- Flag single points of failure (one airframe owns all high-priority strikes)

**Typical gaps to hunt:** over-concentration on one axis; no reserve aircraft; no alternate recovery base.

### B / `synchronized` — Timed combined effects

**Objective:** Produce effects that are meaningful **in combination**—e.g. strikes inside a shared TOT band, ISR positioned for BDA within a defined lag, mutual support between packages.

**Guidelines:**
- Every strike in a sync group has an explicit nominal TOT or window
- BDA/collection tasks reference the strike they support and a max lag
- Routes may be longer if they buy a common hold/IP or observation geometry
- Desynchronization (early/late relative to window) is a first-class failure mode

**Typical gaps to hunt:** strike without BDA plan; ISR arriving after the lag window; no buffer for weather/slip; dependencies on a single sensor platform.

### C / `maneuver` + unexpected axis — Dislocation / surprise geometry

**Objective:** Approach or sequence tasks so the **axis and timing** are not the ones the adversary is most likely postured against (e.g. not the direct radial from the main operating base).

**Guidelines:**
- Forced vias or corridor constraints are explicit and published (no invented points)
- Comparison must show difference from the efficient direct option
- Accept higher fuel/time cost only while remaining GO on reserves
- State the deception or dislocation hypothesis in the option notes (“enemy expects PSAB-direct; we enter from the west”)

**Typical gaps to hunt:** vias that are “unexpected” only on the map but still predictable; logistics tail on the long axis; loss of surprise if timing is slow; no branch if the corridor is closed.

### `shock` — Rapid dominance (contingency archetype)

**Objective:** Front-load massed effects against C2, air defenses, or key nodes so follow-on tasks face a degraded opponent.

**Guidelines:**
- Opening package composition and sequence are explicit
- Success depends on early tasks actually being executable (GO + allocated)
- Define what “enough degradation” means for follow-on options

**Typical gaps to hunt:** no assessment mechanism after the opening blow; fragile dependence on perfect first-look intelligence; no attrition fallback if shock fails.

### `attrition` / resilience (contingency archetype)

**Objective:** Remain able to continue the mission after losses or denied axes; prioritize redundancy over elegance.

**Guidelines:**
- Critical tasks have alternate aircraft or delayed second waves where possible
- Routes prefer recoverable geometry and fuel margin over minimal distance
- Explicitly list what the force can still do if Option A/B/C primary paths fail

**Typical gaps to hunt:** all high-value tasks on one platform type; no re-attack plan; recovery bases saturated.

### `surprise` (often combined with C)

**Objective:** Achieve designated effects before the enemy’s decision cycle catches up.

**Guidelines:**
- Timing and axis choices must be justified against an assumed enemy posture
- Have a branch if surprise is compromised (detect, abort, or accelerate)
- Do not treat surprise as a substitute for fuel feasibility or task coverage

---

## 4. Top-three vs contingency pool

```text
┌─────────────────────────────────────────────┐
│  Contingency pool (many Mission Options)    │
│  each with archetype + saved router inputs  │
└───────────────────┬─────────────────────────┘
                    │ pin
        ┌───────────┼───────────┐
        ▼           ▼           ▼
     Slot A      Slot B      Slot C
   efficient  synchronized  unexpected
   (working comparison set — always visible)
```

- **Pool:** unlimited named options (branches, weather alts, “if corridor closed,” pure shock opening, etc.).
- **Slots A/B/C:** the three the planner actively compares; defaults map to efficient / synchronized / unexpected-axis but can be re-pinned to any archetype.
- Progress = improving quality of the pinned set *and* having credible contingencies for identified risks.

---

## 5. Guidelines for later AI gap / risk / dependency assessment

AI (or a rules engine) should **not** pick the “best” option. It should stress each option against the archetype’s own objectives.

### Per-option checklist (archetype-aware)

1. **Coverage:** Critical tasks allocated and proximity-satisfied?
2. **Feasibility:** All tasked aircraft GO on fuel reserves?
3. **Archetype fit:** Does geometry/timing match the stated approach (e.g. C still looks like A)?
4. **Single points of failure:** One airframe, one navaid corridor, one sensor for BDA?
5. **Dependencies:** Ordered pairs (strike → BDA, SEAD → package, tanker → long axis)—are they explicit?
6. **Branch emptiness:** If this option’s key assumption fails, is there a pinned or pooled contingency?
7. **Desync risk (B):** Windows without margin?
8. **Surprise decay (C/surprise):** Time-to-effect vs assumed enemy reaction time?

### Cross-option checklist

- Do A/B/C actually differ on the dimensions that matter, or are they clones?
- Is there at least one resilient/attrition-flavored contingency if the maneuver option is denied?
- Are synchronized dependencies only present in B, or silently assumed in A/C?

### Output form (for future implementation)

```text
GapReport
  option_id
  archetype
  gaps: [{ code, severity, narrative, related_task_ids? }]
  risks: [{ code, likelihood, impact, mitigation_hint }]
  dependencies: [{ from, to, kind: timing|platform|corridor }]
  missing_contingency_hints: [text]
```

Human remains decision authority; AI surfaces structure.

---

## 6. Link to route mechanics

| Archetype | Router emphasis |
|-----------|-----------------|
| efficient | Minimal vias; civil shortest-path supplier |
| synchronized | Shared holds/IPs; timing metadata; may lengthen legs |
| unexpected / maneuver / surprise | Forced via lists / corridor costs; compare against efficient baseline |
| shock | Front-loaded task priority order; same geometry tools |
| attrition | Prefer margin, alternates; optional second-wave task sets |

Fuel GO/NO-GO remains universal and non-negotiable across all archetypes.

---

## 7. References (conceptual)

- Historical cases above are teaching exemplars for *approach type*, not templates to copy geographically.
- Existing product docs: `CONOPS.md`, `MISSION-ROUTE-DEV-GUIDE.md`, `CIVIL-ROUTE-DEV-GUIDE.md`.
- Boyd / OODA and classical operational art (dislocation vs destruction) inform maneuver vs attrition contrast.
- Kill-chain / TBO literature informs synchronized effects.

---

## 8. Non-goals

- Encoding full doctrine manuals or legal ROE
- Automated selection of a single winning option
- Claiming historical analogy guarantees success in a new theater
- Replacing commander’s intent with archetype labels alone
