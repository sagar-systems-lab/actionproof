from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import AsyncIterator, Protocol

from pydantic import BaseModel, ConfigDict, Field


class RuntimeEventType(str, Enum):
    SCENARIO_STARTED = "SCENARIO_STARTED"
    INCIDENT_CREATED = "INCIDENT_CREATED"
    AGENT_INTENT_CREATED = "AGENT_INTENT_CREATED"
    ACTION_NORMALIZED = "ACTION_NORMALIZED"
    MOSS_QUERY_STARTED = "MOSS_QUERY_STARTED"
    MOSS_QUERY_COMPLETED = "MOSS_QUERY_COMPLETED"
    CONTEXT_VALIDATED = "CONTEXT_VALIDATED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    PROOF_CREATED = "PROOF_CREATED"
    ACTION_ALLOWED = "ACTION_ALLOWED"
    ACTION_BLOCKED = "ACTION_BLOCKED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    POSTFLIGHT_VERIFIED = "POSTFLIGHT_VERIFIED"
    POSTFLIGHT_FAILED = "POSTFLIGHT_FAILED"


class RuntimeEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sequence: int = Field(ge=1)
    trace_id: str = Field(min_length=1)
    event: RuntimeEventType
    timestamp: datetime
    summary: str = Field(min_length=1)


class RuntimeEventSink(Protocol):
    def record(
        self,
        event: RuntimeEventType,
        *,
        trace_id: str,
        summary: str,
    ) -> RuntimeEvent: ...


class FlightRecorder:
    """Append-only in-memory recorder used by the demo runtime and SSE stream."""

    def __init__(self) -> None:
        self._events: list[RuntimeEvent] = []
        self._subscribers: set[asyncio.Queue[RuntimeEvent]] = set()

    @property
    def last_sequence(self) -> int:
        return self._events[-1].sequence if self._events else 0

    def record(
        self,
        event: RuntimeEventType,
        *,
        trace_id: str,
        summary: str,
    ) -> RuntimeEvent:
        item = RuntimeEvent(
            sequence=self.last_sequence + 1,
            trace_id=trace_id,
            event=event,
            timestamp=datetime.now(timezone.utc),
            summary=summary,
        )
        self._events.append(item)
        for queue in tuple(self._subscribers):
            queue.put_nowait(item)
        return item

    def snapshot(self, *, after_sequence: int = 0) -> tuple[RuntimeEvent, ...]:
        return tuple(
            item for item in self._events if item.sequence > after_sequence
        )

    async def stream(
        self,
        *,
        after_sequence: int = 0,
    ) -> AsyncIterator[RuntimeEvent]:
        queue: asyncio.Queue[RuntimeEvent] = asyncio.Queue()
        self._subscribers.add(queue)
        cursor = after_sequence
        try:
            for item in self.snapshot(after_sequence=after_sequence):
                cursor = max(cursor, item.sequence)
                yield item

            while True:
                item = await queue.get()
                if item.sequence <= cursor:
                    continue
                cursor = item.sequence
                yield item
        finally:
            self._subscribers.discard(queue)
