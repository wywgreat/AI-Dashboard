from __future__ import annotations

from fastapi import FastAPI, Query

from backend.services.hf_trending import get_trending_datasets, get_trending_models

app = FastAPI(title="AI Dashboard Backend")


@app.get("/api/hf/trending/models")
def hf_trending_models(limit: int = Query(default=10, ge=1, le=100)) -> dict:
    return get_trending_models(limit=limit)


@app.get("/api/hf/trending/datasets")
def hf_trending_datasets(limit: int = Query(default=10, ge=1, le=100)) -> dict:
    return get_trending_datasets(limit=limit)
