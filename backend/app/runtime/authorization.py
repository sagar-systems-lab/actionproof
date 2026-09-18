from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from app.models.action import NormalizedAction
from app.models.decision import DecisionStatus
from app.models.scenario import EvaluationResult


class AuthorizationError(RuntimeError):
    pass


class ExecutionPermit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    token: str = Field(min_length=16)
    proof_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    action_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


@dataclass
class _Grant:
    proof_id: str
    trace_id: str
    action_hash: str
    consumed: bool = False


def action_fingerprint(action: NormalizedAction) -> str:
    canonical = {
        "tool": action.tool.value,
        "operation": action.operation.value,
        "arguments": action.arguments,
        "incident_id": action.incident_id,
    }
    payload = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class ProofAuthority:
    """Mints single-use execution permits only from an ALLOW proof."""

    def __init__(self) -> None:
        self._grants: dict[str, _Grant] = {}

    def issue(self, result: EvaluationResult) -> ExecutionPermit:
        if result.decision.status is not DecisionStatus.ALLOW:
            raise AuthorizationError("only an ALLOW decision can authorize execution")
        if result.proof.decision is not DecisionStatus.ALLOW:
            raise AuthorizationError("proof does not authorize execution")
        if result.proof.action != result.action:
            raise AuthorizationError("proof action does not match evaluated action")
        if result.proof.trace_id != result.action.trace_id:
            raise AuthorizationError("proof trace does not match evaluated action")

        digest = action_fingerprint(result.action)
        token = secrets.token_urlsafe(32)
        self._grants[token] = _Grant(
            proof_id=result.proof.proof_id,
            trace_id=result.action.trace_id,
            action_hash=digest,
        )
        return ExecutionPermit(
            token=token,
            proof_id=result.proof.proof_id,
            trace_id=result.action.trace_id,
            action_hash=digest,
        )

    def validate_and_consume(
        self,
        action: NormalizedAction,
        permit: ExecutionPermit,
    ) -> None:
        grant = self._grants.get(permit.token)
        if grant is None:
            raise AuthorizationError("execution permit is unknown")
        if grant.consumed:
            raise AuthorizationError("execution permit has already been consumed")
        if permit.proof_id != grant.proof_id or permit.trace_id != grant.trace_id:
            raise AuthorizationError("execution permit metadata is invalid")
        if permit.action_hash != grant.action_hash:
            raise AuthorizationError("execution permit action binding is invalid")
        if action.trace_id != grant.trace_id:
            raise AuthorizationError("action trace does not match execution permit")
        if action_fingerprint(action) != grant.action_hash:
            raise AuthorizationError(
                "action changed after authorization; execution denied"
            )

        grant.consumed = True
