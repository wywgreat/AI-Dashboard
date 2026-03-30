from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

NormalizedRecord = dict[str, Any]


class SourceCollector(Protocol):
    """统一信息源接口：返回标准化后的记录列表。"""

    name: str

    def fetch(self) -> list[NormalizedRecord]:
        """拉取并返回标准化记录。"""


@dataclass
class SourceStatus:
    source: str
    status: str
    record_count: int
    last_synced_at: str | None
    error: str | None = None


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, SourceCollector] = {}

    def register(self, source: SourceCollector) -> None:
        self._sources[source.name] = source

    def list_sources(self) -> list[str]:
        return sorted(self._sources.keys())

    def fetch_all(self) -> tuple[dict[str, list[NormalizedRecord]], list[SourceStatus]]:
        snapshot: dict[str, list[NormalizedRecord]] = {}
        statuses: list[SourceStatus] = []

        for source_name in self.list_sources():
            source = self._sources[source_name]
            try:
                records = source.fetch()
                snapshot[source_name] = records
                statuses.append(
                    SourceStatus(
                        source=source_name,
                        status="ok",
                        record_count=len(records),
                        last_synced_at=datetime.now(timezone.utc).isoformat(),
                        error=None,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                snapshot[source_name] = []
                statuses.append(
                    SourceStatus(
                        source=source_name,
                        status="error",
                        record_count=0,
                        last_synced_at=datetime.now(timezone.utc).isoformat(),
                        error=str(exc),
                    )
                )

        return snapshot, statuses


registry = SourceRegistry()
