from collectors.registry import NormalizedRecord


class MarketSource:
    name = "market"

    def fetch(self) -> list[NormalizedRecord]:
        return [
            {
                "id": "market-1",
                "title": "AAPL",
                "category": "equity",
                "timestamp": "2026-03-30T00:00:00Z",
                "payload": {"price": 214.22, "currency": "USD"},
            }
        ]
