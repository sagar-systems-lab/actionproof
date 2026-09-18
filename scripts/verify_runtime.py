from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import MossSettings
from app.models.decision import DecisionCode
from app.runtime.events import RuntimeEventType
from app.runtime.factory import build_closed_loop_runtime
from app.runtime.models import PostflightStatus


async def main() -> None:
    load_dotenv(ROOT / ".env")
    settings = MossSettings.from_env()
    runtime = build_closed_loop_runtime(settings)

    result = await runtime.run_hero_scenario("INC-104")
    event_types = {item.event for item in result.events}

    print(
        "blocked_restart="
        f"{result.blocked_restart.decision.code.value}"
    )
    print(
        "safe_next_action="
        f"{result.blocked_restart.decision.recommended_next_action}"
    )
    print(
        "recovery_decision="
        f"{result.recovery.evaluation.decision.code.value}"
    )
    print(
        "postflight="
        f"{result.recovery.postflight.status.value}"
    )
    print(
        "retry_restart="
        f"{result.retry_restart.decision.code.value}"
    )
    print(
        "final_reconciliation="
        f"{result.final_state.reconciliation.value}"
    )
    print(f"events={len(result.events)}")

    if (
        result.blocked_restart.decision.code
        is not DecisionCode.BLOCK_RECONCILIATION_REQUIRED
    ):
        raise SystemExit("unsafe restart did not block")
    if (
        result.blocked_restart.decision.recommended_next_action
        != "run_reconciliation"
    ):
        raise SystemExit("safe recovery action was not surfaced")
    if result.recovery.postflight.status is not PostflightStatus.VERIFIED:
        raise SystemExit("reconciliation postflight did not verify")
    if result.retry_restart.decision.code is not DecisionCode.ALLOW_SAFE_STATE:
        raise SystemExit("restart retry was not allowed")

    required_events = {
        RuntimeEventType.SCENARIO_STARTED,
        RuntimeEventType.INCIDENT_CREATED,
        RuntimeEventType.AGENT_INTENT_CREATED,
        RuntimeEventType.ACTION_NORMALIZED,
        RuntimeEventType.MOSS_QUERY_STARTED,
        RuntimeEventType.MOSS_QUERY_COMPLETED,
        RuntimeEventType.CONTEXT_VALIDATED,
        RuntimeEventType.POLICY_EVALUATED,
        RuntimeEventType.PROOF_CREATED,
        RuntimeEventType.ACTION_BLOCKED,
        RuntimeEventType.ACTION_ALLOWED,
        RuntimeEventType.ACTION_EXECUTED,
        RuntimeEventType.POSTFLIGHT_VERIFIED,
    }
    missing = required_events - event_types
    if missing:
        raise SystemExit(
            "missing runtime events: "
            + ",".join(sorted(item.value for item in missing))
        )

    print("RUNTIME_LIVE_VERIFY=PASS")


if __name__ == "__main__":
    asyncio.run(main())
