from __future__ import annotations

from collectors.huggingface.trending import fetch_trending


def get_trending_models(limit: int = 10) -> dict:
    data = fetch_trending(limit=limit)
    return {
        "items": data["top_models"][:limit],
        "stale": data.get("stale", False),
        "captured_at": data.get("captured_at"),
    }


def get_trending_datasets(limit: int = 10) -> dict:
    data = fetch_trending(limit=limit)
    return {
        "items": data["top_datasets"][:limit],
        "stale": data.get("stale", False),
        "captured_at": data.get("captured_at"),
    }
