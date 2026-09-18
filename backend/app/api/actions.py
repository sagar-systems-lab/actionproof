from fastapi import APIRouter, HTTPException

from app.agent.normalizer import NormalizationError
from app.core.engine import ActionProofEngine
from app.models.scenario import EvaluationRequest, EvaluationResult

router = APIRouter(prefix="/api", tags=["actions"])
engine = ActionProofEngine()


@router.post("/evaluate", response_model=EvaluationResult)
def evaluate_action(request: EvaluationRequest) -> EvaluationResult:
    try:
        return engine.evaluate(request)
    except NormalizationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
