from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])


@router.get("/status")
def retrieval_status() -> dict[str, object]:
    configured = bool(
        os.getenv("MOSS_PROJECT_ID", "").strip()
        and os.getenv("MOSS_PROJECT_KEY", "").strip()
    )
    return {
        "configured": configured,
        "environment": os.getenv("ACTIONPROOF_ENV", "production"),
        "indexes": {
            "policy": os.getenv("MOSS_POLICY_INDEX", "actionproof-policy"),
            "knowledge": os.getenv("MOSS_KNOWLEDGE_INDEX", "actionproof-knowledge"),
            "live_state": os.getenv("MOSS_LIVE_STATE_INDEX", "actionproof-live-state"),
        },
    }
