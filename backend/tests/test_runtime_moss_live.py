from __future__ import annotations

import asyncio

import pytest

from app.core.config import MossConfigurationError, MossSettings
from app.models.decision import DecisionCode
from app.runtime.factory import build_closed_loop_runtime
from app.runtime.models import PostflightStatus

pytestmark = pytest.mark.moss_live


def settings_or_skip() -> MossSettings:
    try:
        return MossSettings.from_env()
    except MossConfigurationError:
        pytest.skip("live Moss credentials are not configured")


def test_live_moss_closed_loop_runtime() -> None:
    settings = settings_or_skip()

    async def run() -> None:
        runtime = build_closed_loop_runtime(settings)
        result = await runtime.run_hero_scenario("INC-104")

        assert (
            result.blocked_restart.decision.code
            is DecisionCode.BLOCK_RECONCILIATION_REQUIRED
        )
        assert (
            result.blocked_restart.decision.recommended_next_action
            == "run_reconciliation"
        )
        assert result.recovery.postflight.status is PostflightStatus.VERIFIED
        assert result.retry_restart.decision.code is DecisionCode.ALLOW_SAFE_STATE
        assert result.final_state.reconciliation.value == "COMPLETE"

    asyncio.run(run())
