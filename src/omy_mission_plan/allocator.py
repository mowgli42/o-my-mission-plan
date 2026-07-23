"""Simple regional task allocator.

Groups tasks by crude geographic region, assigns each group to a suitable
aircraft (type preference + availability), and always returns both
allocations and the list of unallocated tasks.
"""

from __future__ import annotations

from collections import defaultdict

from .geo import haversine_nmi
from .models import Aircraft, AircraftType, AllocationResult, LatLon, Task, TaskType

# Capability preference: which aircraft types may fly which task types.
_CAPABLE: dict[TaskType, set[AircraftType]] = {
    TaskType.ISR: {AircraftType.ISR, AircraftType.FIGHTER},
    TaskType.STRIKE: {AircraftType.FIGHTER, AircraftType.BOMBER},
}

# Preferred type first for each task type.
_PREFERRED: dict[TaskType, AircraftType] = {
    TaskType.ISR: AircraftType.ISR,
    TaskType.STRIKE: AircraftType.FIGHTER,
}


def _region_key(location: LatLon, cell_deg: float = 0.75) -> tuple[int, int]:
    """Bucket lat/lon into coarse cells (~45 nmi on a side at mid latitudes)."""
    return (int(location.lat // cell_deg), int(location.lon // cell_deg))


def _centroid(tasks: list[Task]) -> LatLon:
    lat = sum(t.location.lat for t in tasks) / len(tasks)
    lon = sum(t.location.lon for t in tasks) / len(tasks)
    return LatLon(lat=lat, lon=lon)


def aircraft_by_id(aircraft: list[Aircraft], aircraft_id: str) -> Aircraft:
    for a in aircraft:
        if a.id == aircraft_id:
            return a
    raise KeyError(aircraft_id)


def allocate(
    tasks: list[Task],
    aircraft: list[Aircraft],
    airbases: dict,
) -> AllocationResult:
    """Allocate task groups to aircraft; report residuals explicitly."""
    if not tasks:
        return AllocationResult(
            assignments={a.id: [] for a in aircraft},
            unallocated_task_ids=[],
        )

    # Group by region + task type so ISR and strike don't mix blindly.
    buckets: dict[tuple, list[Task]] = defaultdict(list)
    for task in tasks:
        key = (_region_key(task.location), task.type)
        buckets[key].append(task)

    groups = sorted(
        buckets.values(),
        key=lambda g: (-len(g), -max(t.priority for t in g)),
    )

    available = {a.id: a for a in aircraft}
    assignments: dict[str, list[str]] = {a.id: [] for a in aircraft}
    unallocated: list[str] = []
    notes: list[str] = []

    for group in groups:
        task_type = group[0].type
        capable_ids = [
            aid for aid, a in available.items() if a.type in _CAPABLE[task_type]
        ]
        if not capable_ids:
            unallocated.extend(t.id for t in group)
            notes.append(
                f"No capable aircraft left for {task_type.value} group "
                f"({', '.join(t.id for t in group)})"
            )
            continue

        centroid = _centroid(group)
        preferred = _PREFERRED[task_type]

        def score(aid: str) -> tuple:
            a = available[aid]
            dist = haversine_nmi(airbases[a.home_base_id].location, centroid)
            pref_rank = 0 if a.type == preferred else 1
            load = len(assignments[aid])
            return (pref_rank, load, dist)

        chosen_id = min(capable_ids, key=score)
        chosen = available[chosen_id]
        tids = [t.id for t in group]
        assignments[chosen_id].extend(tids)
        del available[chosen_id]
        notes.append(f"Assigned {tids} → {chosen_id} ({chosen.type.value})")

    if unallocated:
        notes.append(f"Unallocated tasks: {unallocated}")

    return AllocationResult(
        assignments=assignments,
        unallocated_task_ids=unallocated,
        notes=notes,
    )
