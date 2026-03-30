from fastapi import FastAPI

app = FastAPI(title="AI Dashboard API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/sources")
def list_sources() -> dict[str, list[dict[str, str]]]:
    return {
        "sources": [
            {"id": "aa-tech", "name": "AA Tech"},
            {"id": "aa-research", "name": "AA Research"},
            {"id": "aa-products", "name": "AA Products"},
            {"id": "hf-trending", "name": "HF Trending"},
        ]
    }
