from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class AARow(BaseModel):
    source: str
    table: str
    model: str
    provider: Optional[str] = None
    country: Optional[str] = None
    intelligence_score: Optional[float] = None
    cost_metric: Optional[float] = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AAResponse(BaseModel):
    source: str
    table: str
    captured_at: datetime
    rows: list[AARow]
    from_cache: bool = False
