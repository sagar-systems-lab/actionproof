from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class MossConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class MossSettings:
    project_id: str
    project_key: str
    policy_index: str = "actionproof-policy"
    knowledge_index: str = "actionproof-knowledge"
    live_state_index: str = "actionproof-live-state"
    environment: str = "production"
    model_id: str = "moss-minilm"

    @classmethod
    def from_env(cls) -> "MossSettings":
        repo_env = Path(__file__).resolve().parents[3] / ".env"
        load_dotenv(repo_env, override=False)

        project_id = os.getenv("MOSS_PROJECT_ID", "").strip()
        project_key = os.getenv("MOSS_PROJECT_KEY", "").strip()

        if not project_id or not project_key:
            raise MossConfigurationError(
                "MOSS_PROJECT_ID and MOSS_PROJECT_KEY are required for retrieval."
            )

        return cls(
            project_id=project_id,
            project_key=project_key,
            policy_index=os.getenv("MOSS_POLICY_INDEX", "actionproof-policy").strip(),
            knowledge_index=os.getenv(
                "MOSS_KNOWLEDGE_INDEX", "actionproof-knowledge"
            ).strip(),
            live_state_index=os.getenv(
                "MOSS_LIVE_STATE_INDEX", "actionproof-live-state"
            ).strip(),
            environment=os.getenv("ACTIONPROOF_ENV", "production").strip(),
            model_id=os.getenv("MOSS_MODEL_ID", "moss-minilm").strip(),
        )
