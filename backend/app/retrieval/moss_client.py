from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
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

        self._live_session = None
        self._live_session_lock = asyncio.Lock()

        self._local_sessions: dict[str, object] = {}
        self._local_ready = False
        self._local_lock = asyncio.Lock()

    async def start(self) -> None:
        if self.settings.runtime_mode == "local":
            await self._ensure_local_runtime()
            return

        await asyncio.gather(
            self._ensure_loaded(self.settings.policy_index),
            self._ensure_loaded(self.settings.knowledge_index),
            self._ensure_live_session(),
        )

    async def query(
        self,
        requirement: ContextRequirement,
        *,
        incident_id: str,
    ) -> list[RawRetrievedDocument]:
        if self.settings.runtime_mode == "local":
            return await self._query_local_runtime(
                requirement,
                incident_id=incident_id,
            )

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

    async def _query_local_runtime(
        self,
        requirement: ContextRequirement,
        *,
        incident_id: str,
    ) -> list[RawRetrievedDocument]:
        await self._ensure_local_runtime()
        index_name = self._index_name(requirement.domain)
        session = self._local_sessions[index_name]

        if (
            requirement.domain is RetrievalDomain.LIVE_STATE
            and requirement.incident_scoped
        ):
            return await self._get_local_live_state(
                session,
                requirement=requirement,
                incident_id=incident_id,
            )

        try:
            result = await session.query(
                requirement.query,
                QueryOptions(
                    top_k=max(requirement.top_k, int(session.doc_count)),
                    alpha=0.65,
                ),
            )
        except Exception as exc:
            raise MossUnavailableError(
                f"Moss local query failed for {requirement.key}: {exc}"
            ) from exc

        source_types = {item.value for item in requirement.source_types}
        documents: list[RawRetrievedDocument] = []

        for doc in result.docs:
            metadata = dict(doc.metadata or {})
            if metadata.get("environment") != self.settings.environment:
                continue
            if metadata.get("source_type") not in source_types:
                continue
            if (
                requirement.incident_scoped
                and metadata.get("incident_id") != incident_id
            ):
                continue

            documents.append(
                RawRetrievedDocument(
                    document_id=doc.id,
                    index_name=index_name,
                    content=doc.text,
                    score=float(doc.score),
                    metadata=metadata,
                )
            )
            if len(documents) >= requirement.top_k:
                break

        return documents

    async def _get_local_live_state(
        self,
        session,
        *,
        requirement: ContextRequirement,
        incident_id: str,
    ) -> list[RawRetrievedDocument]:
        document_id = f"STATE-{incident_id}"
        try:
            docs = await session.get_docs()
        except Exception as exc:
            raise MossUnavailableError(
                f"Moss local live-state read failed for {requirement.key}: {exc}"
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

    async def _get_live_state(
        self,
        *,
        requirement: ContextRequirement,
        incident_id: str,
    ) -> list[RawRetrievedDocument]:
        document_id = f"STATE-{incident_id}"
        try:
            session = await self._ensure_live_session()
            docs = await session.get_docs()
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

        if self.settings.runtime_mode == "local":
            await self._ensure_local_runtime()
            session = self._local_sessions.get(index_name)
            if session is None:
                return []
            try:
                docs = await session.get_docs()
            except Exception as exc:
                raise MossUnavailableError(
                    f"Moss local document lookup failed for '{index_name}': {exc}"
                ) from exc
        else:
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

        if self.settings.runtime_mode == "local":
            await self._ensure_local_runtime()
            session = self._local_sessions.get(name)
            if session is None:
                session = await self._create_local_session(name)
                self._local_sessions[name] = session
            await session.add_docs(docs)
            return

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

        try:
            if self.settings.runtime_mode == "local":
                await self._ensure_local_runtime()
                session = self._local_sessions[self.settings.live_state_index]
            else:
                session = await self._ensure_live_session()
            await session.add_docs([document])
        except Exception as exc:
            raise MossUnavailableError(
                f"Moss live-state update failed for '{incident_id}': {exc}"
            ) from exc

    async def _ensure_local_runtime(self) -> None:
        if self._local_ready:
            return

        async with self._local_lock:
            if self._local_ready:
                return

            try:
                policy = await self._create_local_session(self.settings.policy_index)
                knowledge = await self._create_local_session(self.settings.knowledge_index)
                live_state = await self._create_local_session(
                    self.settings.live_state_index
                )

                self._local_sessions = {
                    self.settings.policy_index: policy,
                    self.settings.knowledge_index: knowledge,
                    self.settings.live_state_index: live_state,
                }

                datasets = self._local_seed_documents()
                await policy.add_docs(datasets[self.settings.policy_index])
                await knowledge.add_docs(datasets[self.settings.knowledge_index])
                await live_state.add_docs(datasets[self.settings.live_state_index])
            except Exception as exc:
                self._local_sessions = {}
                raise MossUnavailableError(
                    f"failed to initialize local Moss runtime: {exc}"
                ) from exc

            self._local_ready = True

    async def _create_local_session(self, name: str):
        try:
            from moss.client.session_index import SessionIndex

            session = SessionIndex._create(
                name=name,
                model_id=self.settings.model_id,
                project_id=self.settings.project_id,
                project_key=self.settings.project_key,
            )
            if getattr(session, "_model_id", self.settings.model_id) != "custom":
                await session._get_embedding_service()
            return session
        except Exception as exc:
            raise MossUnavailableError(
                f"failed to create local Moss session '{name}': {exc}"
            ) from exc

    def _local_seed_documents(self) -> dict[str, list[DocumentInfo]]:
        root = Path(__file__).resolve().parents[3]
        now = datetime.now(timezone.utc).isoformat()

        sources = {
            self.settings.policy_index: root / "data" / "policies" / "policies.json",
            self.settings.knowledge_index: root / "data" / "runbooks" / "knowledge.json",
            self.settings.live_state_index: root / "data" / "incidents" / "live-state.json",
        }

        result: dict[str, list[DocumentInfo]] = {}
        for index_name, path in sources.items():
            payload = json.loads(path.read_text(encoding="utf-8"))
            documents: list[DocumentInfo] = []
            for item in payload:
                metadata = {
                    str(key): str(value)
                    for key, value in item["metadata"].items()
                }
                metadata["environment"] = self.settings.environment
                if metadata.get("updated_at") == "$NOW":
                    metadata["updated_at"] = now

                documents.append(
                    DocumentInfo(
                        id=item["id"],
                        text=item["text"],
                        metadata=metadata,
                    )
                )
            result[index_name] = documents

        return result

    async def _ensure_live_session(self):
        if self._live_session is not None:
            return self._live_session

        async with self._live_session_lock:
            if self._live_session is not None:
                return self._live_session
            try:
                self._live_session = await self._client.session(
                    index_name=self.settings.live_state_index,
                )
            except Exception as exc:
                raise MossUnavailableError(
                    f"failed to open Moss live-state session: {exc}"
                ) from exc
            return self._live_session

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
