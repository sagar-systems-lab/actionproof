import asyncio

from app.retrieval.engine import RetrievalActionProofEngine
from app.retrieval.retriever import MossContextRetriever

from tests.retrieval_fakes import StatefulFakeMossBackend


def test_preflight_exposes_nanosecond_stage_measurements(
    restart_intent,
    unsafe_state,
) -> None:
    backend = StatefulFakeMossBackend(state=unsafe_state)
    engine = RetrievalActionProofEngine(
        MossContextRetriever(backend, environment="production")
    )

    result = asyncio.run(engine.evaluate(restart_intent))
    latency = result.proof.latency

    assert latency.normalization_ns > 0
    assert latency.context_resolve_ns > 0
    assert latency.moss_retrieval_ns > 0
    assert latency.freshness_ns > 0
    assert latency.policy_eval_ns > 0
    assert latency.proof_build_ns > 0
    assert latency.total_preflight_ns > 0

    assert latency.retrieval_us == latency.moss_retrieval_ns // 1_000
    assert latency.freshness_us == latency.freshness_ns // 1_000
    assert latency.policy_us == latency.policy_eval_ns // 1_000
    assert latency.proof_us == latency.proof_build_ns // 1_000
    assert latency.total_us == latency.total_preflight_ns // 1_000
