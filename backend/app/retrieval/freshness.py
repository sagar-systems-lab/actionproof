from __future__ import annotations

from datetime import datetime, timezone

from app.models.context import ContextFreshness


class FreshnessEngine:
    def classify(
        self,
        updated_at: datetime | None,
        ttl_seconds: int | None,
        *,
        now: datetime | None = None,
    ) -> ContextFreshness:
        if updated_at is None or ttl_seconds is None or ttl_seconds <= 0:
            return ContextFreshness.UNKNOWN

        if updated_at.tzinfo is None or updated_at.utcoffset() is None:
            return ContextFreshness.UNKNOWN

        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("now must include a timezone")

        age_seconds = (current - updated_at).total_seconds()
        if age_seconds < 0:
            return ContextFreshness.UNKNOWN

        if age_seconds <= ttl_seconds:
            return ContextFreshness.FRESH
        return ContextFreshness.STALE
