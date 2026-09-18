import json
from pathlib import Path

import pytest

from app.core.engine import ActionProofEngine
from app.models.scenario import EvaluationRequest

SCENARIO_DIR = Path(__file__).parents[2] / "data" / "scenarios"
SCENARIOS = [
    "safe-restart.json",
    "unsafe-restart.json",
    "missing-context.json",
    "stale-context.json",
]


@pytest.mark.parametrize("filename", SCENARIOS)
def test_scenario_contract(filename: str) -> None:
    payload = json.loads((SCENARIO_DIR / filename).read_text(encoding="utf-8"))
    request = EvaluationRequest.model_validate(payload["request"])

    result = ActionProofEngine().evaluate(request)

    assert result.decision.status.value == payload["expected"]["decision"]
    assert result.decision.code.value == payload["expected"]["code"]
    assert result.proof.decision.value == payload["expected"]["decision"]
