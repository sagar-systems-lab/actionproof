from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.agent.normalizer import NormalizationError
from app.core.config import MossConfigurationError, MossSettings
from app.models.scenario import EvaluationResult, MossEvaluationRequest
from app.retrieval.engine import RetrievalActionProofEngine
from app.retrieval.moss_client import MossClient
from app.retrieval.retriever import MossContextRetriever

router = APIRouter(prefix="/api", tags=["actions"])

_engine: RetrievalActionProofEngine | None = None


def get_retrieval_engine() -> RetrievalActionProofEngine:
    global _engine

    if _engine is not None:
        return _engine

    try:
        settings = MossSettings.from_env()
    except MossConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Moss retrieval is not configured.",
        ) from exc

    client = MossClient(settings)
    retriever = MossContextRetriever(
        client,
        environment=settings.environment,
    )
    _engine = RetrievalActionProofEngine(retriever)
    return _engine


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_action(
    request: MossEvaluationRequest,
    engine: RetrievalActionProofEngine = Depends(get_retrieval_engine),
) -> EvaluationResult:
    try:
        return await engine.evaluate(request.intent)
    except NormalizationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
