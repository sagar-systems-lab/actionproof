from __future__ import annotations

import asyncio
import math
from datetime import datetime, timezone
from statistics import median
from time import perf_counter_ns

from app.agent.normalizer import ActionNormalizer
from app.core.config import MossSettings
from app.models.action import ActionIntent
from app.models.state import (
    ConnectionState,
    HealthState,
    OutstandingState,
    ReconciliationState,
    ServiceState,
    SimulatorState,
)
from app.retrieval.moss_client import MossClient
from app.retrieval.resolver import ContextRequirementResolver


SAMPLES = 7
PROFILE_INCIDENT = "PROFILE-MOSS"


def ms(ns: int) -> float:
    return ns / 1_000_000


def nearest_rank(values: list[int], percentile: float) -> int:
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def report(label: str, values: list[int]) -> None:
    print(
        f"{label:<30} "
        f"p50={ms(int(median(values))):8.2f} ms  "
        f"p95={ms(nearest_rank(values, 0.95)):8.2f} ms  "
        f"max={ms(max(values)):8.2f} ms"
    )


async def timed(call):
    started = perf_counter_ns()
    result = await call()
    return perf_counter_ns() - started, result


async def main() -> None:
    settings = MossSettings.from_env()
    client = MossClient(settings)

    print("Loading Moss indexes...")
    await client.start()

    safe = SimulatorState(
        connection=ConnectionState.CONNECTED,
        reconciliation=ReconciliationState.COMPLETE,
        service=ServiceState.RUNNING,
        health=HealthState.HEALTHY,
        outstanding=OutstandingState.CLEAR,
    )
    await client.upsert_live_state(
        PROFILE_INCIDENT,
        safe,
        version="profile-1",
        ttl_seconds=3600,
    )

    intent = ActionIntent(
        action_id="ACTION-PROFILE-MOSS",
        trace_id="TRACE-PROFILE-MOSS",
        actor="profile-agent",
        text="Restart the service.",
        incident_id=PROFILE_INCIDENT,
        timestamp=datetime.now(timezone.utc),
    )
    action = ActionNormalizer().normalize(intent)
    requirements = ContextRequirementResolver().resolve(action)

    print()
    print("=== SEMANTIC / CURRENT PATH BY REQUIREMENT ===")
    for requirement in requirements:
        values: list[int] = []
        for _ in range(SAMPLES):
            elapsed, _ = await timed(
                lambda requirement=requirement: client.query(
                    requirement,
                    incident_id=PROFILE_INCIDENT,
                )
            )
            values.append(elapsed)
        report(requirement.key, values)

    required = tuple(item for item in requirements if item.required)

    full_parallel: list[int] = []
    required_parallel: list[int] = []

    for _ in range(SAMPLES):
        elapsed, _ = await timed(
            lambda: asyncio.gather(
                *[
                    client.query(item, incident_id=PROFILE_INCIDENT)
                    for item in requirements
                ]
            )
        )
        full_parallel.append(elapsed)

        elapsed, _ = await timed(
            lambda: asyncio.gather(
                *[
                    client.query(item, incident_id=PROFILE_INCIDENT)
                    for item in required
                ]
            )
        )
        required_parallel.append(elapsed)

    print()
    print("=== PARALLEL WALL TIME ===")
    report("current_full_4_requirements", full_parallel)
    report("required_only_3", required_parallel)

    exact_targets = {
        "restart_policy": (
            settings.policy_index,
            ("POL-RESTART-001",),
        ),
        "current_state": (
            settings.live_state_index,
            (f"STATE-{PROFILE_INCIDENT}",),
        ),
        "recovery_runbook": (
            settings.knowledge_index,
            ("RB-SERVICE-003",),
        ),
        "incident_history": (
            settings.knowledge_index,
            ("HIST-INC-077",),
        ),
    }

    print()
    print("=== EXACT MOSS DOCUMENT LOOKUP ===")
    exact_samples: dict[str, list[int]] = {key: [] for key in exact_targets}
    for key, (index_name, ids) in exact_targets.items():
        for _ in range(SAMPLES):
            elapsed, docs = await timed(
                lambda index_name=index_name, ids=ids: client.get_by_ids(
                    index_name,
                    ids,
                )
            )
            if not docs:
                raise RuntimeError(f"exact lookup returned no document for {key}")
            exact_samples[key].append(elapsed)
        report(key, exact_samples[key])

    exact_required_parallel: list[int] = []
    exact_all_parallel: list[int] = []

    for _ in range(SAMPLES):
        elapsed, _ = await timed(
            lambda: asyncio.gather(
                *[
                    client.get_by_ids(
                        exact_targets[key][0],
                        exact_targets[key][1],
                    )
                    for key in (
                        "restart_policy",
                        "current_state",
                        "recovery_runbook",
                    )
                ]
            )
        )
        exact_required_parallel.append(elapsed)

        elapsed, _ = await timed(
            lambda: asyncio.gather(
                *[
                    client.get_by_ids(index_name, ids)
                    for index_name, ids in exact_targets.values()
                ]
            )
        )
        exact_all_parallel.append(elapsed)

    print()
    print("=== EXACT LOOKUP WALL TIME ===")
    report("exact_required_3", exact_required_parallel)
    report("exact_all_4", exact_all_parallel)

    print()
    print("MOSS_PATH_PROFILE=PASS")


if __name__ == "__main__":
    asyncio.run(main())
