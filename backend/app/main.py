from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from collectors.registry import registry
from collectors.sources.market import MarketSource
from collectors.sources.news import NewsSource

app = FastAPI(title="AI Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

registry.register(NewsSource())
registry.register(MarketSource())


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard/summary")
def dashboard_summary() -> dict[str, object]:
    snapshot, statuses = registry.fetch_all()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": [status.__dict__ for status in statuses],
        "snapshot": snapshot,
    }
