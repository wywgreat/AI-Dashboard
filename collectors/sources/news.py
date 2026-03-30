from collectors.registry import NormalizedRecord


class NewsSource:
    name = "news"

    def fetch(self) -> list[NormalizedRecord]:
        return [
            {
                "id": "news-1",
                "title": "System launch",
                "category": "announcement",
                "timestamp": "2026-03-30T00:00:00Z",
                "payload": {"priority": "high"},
            }
        ]
