from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import monotonic
from typing import Iterable

from moss import (
    DocumentInfo,
    GetDocumentsOptions,
    MossClient as MossSdkClient,
    MutationOptions,
    QueryOptions,
)

from app.core.config import MossSettings
from app.models.state import SimulatorState

from .schemas import ContextRequirement, RawRetrievedDocument, RetrievalDomain


class MossUnavailableError(RuntimeError):
    pass


class MossClient:
    def __init__(self, settings: MossSettings) -> None:
        self.settings = settings
        self._client = MossSdkClient(settings.project_id, settings.project_key)
        self._loaded: set[str] = set()
        self._load_lock = asyncio.Lock()

    async def start(self) -> None:
        await asyncio.gather(
            self._ensure_loaded(self.settings.policy_index),
            self._ensure_loaded(self.settings.knowledge_index),
        )

    async def query(
        self,
        requirement: ContextRequirement,
        *,
        incident_id: str,
    ) -> list[RawRetrievedDocument]:
        if (
            requirement.domain is RetrievalDomain.LIVE_STATE
            and requirement.incident_scoped
        ):
            return await self._get_live_state(
                requirement=requirement,
                incident_id=incident_id,
            )

        index_name = self._index_name(requirement.domain)
        await self._ensure_loaded(index_name)

        filters: list[dict] = [
            {
                "field": "environment",
                "condition": {"$eq": self.settings.environment},
            }
        ]

        if len(requirement.source_types) == 1:
            filters.append(
                {
                    "field": "source_type",
                    "condition": {"$eq": requirement.source_types[0].value},
                }
            )
        else:
            filters.append(
                {
                    "field": "source_type",
                    "condition": {
                        "$in": [source.value for source in requirement.source_types]
                    },
                }
            )

        if requirement.incident_scoped:
            filters.append(
                {
                    "field": "incident_id",
                    "condition": {"$eq": incident_id},
                }
            )

        try:
            result = await self._client.query(
                index_name,
                requirement.query,
                QueryOptions(
                    top_k=requirement.top_k,
                    alpha=0.65,
                    filter={"$and": filters},
                ),
            )
        except Exception as exc:
            raise MossUnavailableError(
                f"Moss query failed for {requirement.key}: {exc}"
            ) from exc

        return [
            RawRetrievedDocument(
                document_id=doc.id,
                index_name=index_name,
                content=doc.text,
                score=float(doc.score),
                metadata=dict(doc.metadata or {}),
            )
            for doc in result.docs
        ]

    async def _get_live_state(
        self,
        *,
        requirement: ContextRequirement,
        incident_id: str,
    ) -> list[RawRetrievedDocument]:
        document_id = f"STATE-{incident_id}"
        try:
            docs = await self._client.get_docs(
                self.settings.live_state_index,
                GetDocumentsOptions(doc_ids=[document_id]),
            )
        except Exception as exc:
            raise MossUnavailableError(
                f"Moss live-state read failed for {requirement.key}: {exc}"
            ) from exc

        return [
            RawRetrievedDocument(
                document_id=doc.id,
                index_name=self.settings.live_state_index,
                content=doc.text,
                score=1.0,
                metadata=dict(doc.metadata or {}),
            )
            for doc in docs
            if doc.id == document_id
        ]

    async def get_by_ids(
        self,
        index_name: str,
        document_ids: Iterable[str],
    ) -> list[RawRetrievedDocument]:
        ids = tuple(document_ids)
        if not ids:
            return []

        try:
            docs = await self._client.get_docs(
                index_name,
                GetDocumentsOptions(doc_ids=list(ids)),
            )
        except Exception as exc:
            raise MossUnavailableError(
                f"Moss document lookup failed for '{index_name}': {exc}"
            ) from exc

        return [
            RawRetrievedDocument(
                document_id=doc.id,
                index_name=index_name,
                content=doc.text,
                score=1.0,
                metadata=dict(doc.metadata or {}),
            )
            for doc in docs
            if doc.id in ids
        ]

    async def ensure_index(
        self,
        name: str,
        documents: Iterable[DocumentInfo],
    ) -> None:
        docs = list(documents)
        existing = {index.name for index in await self._client.list_indexes()}

        if name in existing:
            mutation = await self._client.add_docs(
                name,
                docs,
                MutationOptions(upsert=True),
            )
        else:
            mutation = await self._client.create_index(
                name,
                docs,
                self.settings.model_id,
            )

        await self._wait_for_job(mutation.job_id)

    async def upsert_live_state(
        self,
        incident_id: str,
        state: SimulatorState,
        *,
        version: str = "1",
        ttl_seconds: int = 30,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        metadata = {
            "source_type": "live_state",
            "authority": "runtime",
            "version": version,
            "environment": self.settings.environment,
            "incident_id": incident_id,
            "updated_at": now,
            "ttl_seconds": str(ttl_seconds),
            "connection": state.connection.value,
            "reconciliation": state.reconciliation.value,
            "service": state.service.value,
            "health": state.health.value,
            "outstanding": state.outstanding.value,
        }
        document = DocumentInfo(
            id=f"STATE-{incident_id}",
            text=(
                f"incident_id={incident_id} "
                f"connection={state.connection.value} "
                f"reconciliation={state.reconciliation.value} "
                f"service={state.service.value} "
                f"health={state.health.value} "
                f"outstanding={state.outstanding.value}"
            ),
            metadata=metadata,
        )

        mutation = await self._client.add_docs(
            self.settings.live_state_index,
            [document],
            MutationOptions(upsert=True),
        )
        await self._wait_for_job(mutation.job_id)

    async def _ensure_loaded(self, index_name: str) -> None:
        if index_name in self._loaded:
            return

        async with self._load_lock:
            if index_name in self._loaded:
                return
            try:
                await self._client.load_index(
                    index_name,
                    auto_refresh=True,
                    polling_interval_in_seconds=2,
                )
            except Exception as exc:
                raise MossUnavailableError(
                    f"failed to load Moss index '{index_name}': {exc}"
                ) from exc
            self._loaded.add(index_name)

    async def _wait_for_job(self, job_id: str, timeout_seconds: float = 60.0) -> None:
        deadline = monotonic() + timeout_seconds
        while True:
            status = await self._client.get_job_status(job_id)
            value = status.status.value
            if value == "completed":
                return
            if value == "failed":
                raise MossUnavailableError(
                    f"Moss mutation failed: {status.error or job_id}"
                )
            if monotonic() >= deadline:
                raise MossUnavailableError(
                    f"Moss mutation timed out: {job_id}"
                )
            await asyncio.sleep(0.25)

    def _index_name(self, domain: RetrievalDomain) -> str:
        if domain is RetrievalDomain.POLICY:
            return self.settings.policy_index
        if domain is RetrievalDomain.KNOWLEDGE:
            return self.settings.knowledge_index
        if domain is RetrievalDomain.LIVE_STATE:
            return self.settings.live_state_index
        raise ValueError(f"unsupported retrieval domain: {domain}")
