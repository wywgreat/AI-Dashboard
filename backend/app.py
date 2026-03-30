from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException

from collectors.artificial_analysis import AACollectorService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(title="AI Dashboard Backend")
collector = AACollectorService()


@app.get("/api/aa/intelligence-index")
def intelligence_index():
    try:
        return collector.collect("intelligence-index")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed collecting intelligence index: {exc}") from exc


@app.get("/api/aa/models-by-country")
def models_by_country():
    try:
        return collector.collect("models-by-country")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed collecting models by country: {exc}") from exc


@app.get("/api/aa/intelligence-vs-cost")
def intelligence_vs_cost():
    try:
        return collector.collect("intelligence-vs-cost")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed collecting intelligence vs cost: {exc}") from exc
