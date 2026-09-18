from __future__ import annotations

from fastapi import APIRouter

from app.core.config import MossConfigurationError, MossSettings

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])


@router.get("/status")
def retrieval_status() -> dict[str, object]:
    try:
        settings = MossSettings.from_env()
    except MossConfigurationError:
        return {
            "configured": False,
            "environment": "production",
            "indexes": {
                "policy": "actionproof-policy",
                "knowledge": "actionproof-knowledge",
                "live_state": "actionproof-live-state",
            },
        }

    return {
        "configured": True,
        "environment": settings.environment,
        "indexes": {
            "policy": settings.policy_index,
            "knowledge": settings.knowledge_index,
            "live_state": settings.live_state_index,
        },
    }
