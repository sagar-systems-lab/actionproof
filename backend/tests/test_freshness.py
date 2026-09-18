from datetime import datetime, timedelta, timezone

from app.models.context import ContextFreshness
from app.retrieval.freshness import FreshnessEngine


def test_fresh_context_within_ttl() -> None:
    now = datetime.now(timezone.utc)
    result = FreshnessEngine().classify(
        now - timedelta(seconds=4),
        5,
        now=now,
    )
    assert result is ContextFreshness.FRESH


def test_context_past_ttl_is_stale() -> None:
    now = datetime.now(timezone.utc)
    result = FreshnessEngine().classify(
        now - timedelta(seconds=6),
        5,
        now=now,
    )
    assert result is ContextFreshness.STALE


def test_missing_freshness_metadata_is_unknown() -> None:
    assert FreshnessEngine().classify(None, None) is ContextFreshness.UNKNOWN


def test_future_timestamp_is_unknown() -> None:
    now = datetime.now(timezone.utc)
    result = FreshnessEngine().classify(
        now + timedelta(seconds=1),
        5,
        now=now,
    )
    assert result is ContextFreshness.UNKNOWN
