from typing import Any

from collectors.registry import SourceRegistry


class DemoSource:
    name = "demo"

    def fetch(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "1",
                "title": "x",
                "category": "demo",
                "timestamp": "2026-03-30T00:00:00Z",
                "payload": {},
            }
        ]


class ErrorSource:
    name = "broken"

    def fetch(self) -> list[dict[str, Any]]:
        raise RuntimeError("boom")


def test_fetch_all_collects_statuses() -> None:
    registry = SourceRegistry()
    registry.register(DemoSource())
    registry.register(ErrorSource())

    snapshot, statuses = registry.fetch_all()

    by_source = {item.source: item for item in statuses}
    assert snapshot["demo"]
    assert snapshot["broken"] == []
    assert by_source["demo"].status == "ok"
    assert by_source["broken"].status == "error"
    assert by_source["broken"].error == "boom"
