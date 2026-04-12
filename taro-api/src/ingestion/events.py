"""Layer 2 event payload for policy ingestion."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


@dataclass
class IngestionEvent:
    """Describes a change in Layer 1 landing content."""

    source_key: str
    op: Literal["upsert", "delete"]
    version: str = ""
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> dict:
        return {
            "source_key": self.source_key,
            "op": self.op,
            "version": self.version,
            "occurred_at": self.occurred_at,
        }

    @classmethod
    def from_json(cls, data: dict) -> "IngestionEvent":
        return cls(
            source_key=data["source_key"],
            op=data["op"],
            version=data.get("version", ""),
            occurred_at=data.get("occurred_at", datetime.now(timezone.utc).isoformat()),
        )
