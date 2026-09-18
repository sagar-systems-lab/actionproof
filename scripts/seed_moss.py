from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from moss import DocumentInfo

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import MossSettings
from app.retrieval.moss_client import MossClient

DATASETS = (
    ("policy_index", ROOT / "data" / "policies" / "policies.json"),
    ("knowledge_index", ROOT / "data" / "runbooks" / "knowledge.json"),
    ("live_state_index", ROOT / "data" / "incidents" / "live-state.json"),
)


def load_documents(path: Path, environment: str) -> list[DocumentInfo]:
    now = datetime.now(timezone.utc).isoformat()
    payload = json.loads(path.read_text(encoding="utf-8"))
    documents: list[DocumentInfo] = []

    for item in payload:
        metadata = {
            str(key): str(value)
            for key, value in item["metadata"].items()
        }
        metadata["environment"] = environment
        if metadata.get("updated_at") == "$NOW":
            metadata["updated_at"] = now

        documents.append(
            DocumentInfo(
                id=item["id"],
                text=item["text"],
                metadata=metadata,
            )
        )

    return documents


async def main() -> None:
    load_dotenv(ROOT / ".env")
    settings = MossSettings.from_env()
    client = MossClient(settings)

    for setting_name, path in DATASETS:
        index_name = getattr(settings, setting_name)
        documents = load_documents(path, settings.environment)
        print(f"Seeding {index_name} ({len(documents)} documents)")
        await client.ensure_index(index_name, documents)

    await client.start()
    print("Moss indexes seeded and loaded.")


if __name__ == "__main__":
    asyncio.run(main())
