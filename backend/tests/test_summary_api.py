import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from backend.app.main import app


def test_dashboard_summary() -> None:
    client = TestClient(app)

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    payload = response.json()
    assert "generated_at" in payload
    assert "sources" in payload
    assert "snapshot" in payload
    assert len(payload["sources"]) >= 2
