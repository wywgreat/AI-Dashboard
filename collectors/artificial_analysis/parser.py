from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from bs4 import BeautifulSoup

from .schemas import AARow

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TableConfig:
    slug: str
    table_name: str
    page_url: str


TABLES: dict[str, TableConfig] = {
    "intelligence-index": TableConfig(
        slug="intelligence-index",
        table_name="Artificial Analysis Intelligence Index",
        page_url="https://artificialanalysis.ai/intelligence-index",
    ),
    "models-by-country": TableConfig(
        slug="models-by-country",
        table_name="Leading Models by Country",
        page_url="https://artificialanalysis.ai/leading-models-by-country",
    ),
    "intelligence-vs-cost": TableConfig(
        slug="intelligence-vs-cost",
        table_name="Intelligence vs. Cost to Run Artificial Analysis Intelligence Index",
        page_url="https://artificialanalysis.ai/intelligence-vs-cost",
    ),
}

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _NUM_RE.search(str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def _warn_missing(row: AARow) -> None:
    missing = [
        name
        for name in ("model", "provider", "country", "intelligence_score", "cost_metric")
        if getattr(row, name) in (None, "")
    ]
    if missing:
        logger.warning(
            "AA row has missing fields", extra={"table": row.table, "model": row.model, "missing": missing}
        )


def _build_row(config: TableConfig, data: dict[str, Any]) -> AARow:
    row = AARow(
        source="artificialanalysis.ai",
        table=config.table_name,
        model=(data.get("model") or data.get("name") or "").strip(),
        provider=(data.get("provider") or data.get("lab") or None),
        country=(data.get("country") or data.get("location") or None),
        intelligence_score=_to_float(data.get("intelligence_score") or data.get("score") or data.get("intelligence")),
        cost_metric=_to_float(data.get("cost_metric") or data.get("cost") or data.get("cost_to_run")),
        captured_at=datetime.now(timezone.utc),
    )
    if not row.model:
        logger.warning("AA row skipped because model is empty", extra={"table": config.table_name, "raw": data})
    else:
        _warn_missing(row)
    return row


def _extract_json_candidates(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict[str, Any]] = []

    for script in soup.select("script[type='application/json'], script#__NEXT_DATA__"):
        payload = (script.string or script.get_text() or "").strip()
        if not payload:
            continue
        try:
            obj = json.loads(payload)
            if isinstance(obj, dict):
                out.append(obj)
        except json.JSONDecodeError:
            logger.warning("Failed to decode embedded JSON script")

    # Some pages inject serialized JSON in script bodies.
    for script in soup.find_all("script"):
        txt = script.get_text(" ", strip=True)
        if "[{" not in txt or "model" not in txt.lower():
            continue
        for raw in re.findall(r"(\{.*\}|\[\{.*\}\])", txt):
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict):
                    out.append(obj)
                elif isinstance(obj, list):
                    out.append({"items": obj})
            except json.JSONDecodeError:
                continue

    return out


def _iter_rows_from_json_like(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, list):
        if obj and all(isinstance(x, dict) for x in obj):
            yield from obj
        else:
            for item in obj:
                yield from _iter_rows_from_json_like(item)
    elif isinstance(obj, dict):
        keys = {k.lower() for k in obj}
        if {"model", "name"} & keys and ({"score", "intelligence", "country", "cost"} & keys):
            yield obj
        for value in obj.values():
            yield from _iter_rows_from_json_like(value)


def parse_from_json_payload(config: TableConfig, payloads: list[dict[str, Any]]) -> list[AARow]:
    rows: list[AARow] = []
    for payload in payloads:
        for candidate in _iter_rows_from_json_like(payload):
            row = _build_row(config, candidate)
            if row.model:
                rows.append(row)
    return rows


def parse_from_html(config: TableConfig, html: str) -> list[AARow]:
    """Fallback parser when no directly consumable JSON/XHR payload is available."""
    soup = BeautifulSoup(html, "html.parser")
    rows: list[AARow] = []

    for tr in soup.select("table tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.select("th, td")]
        if len(cells) < 2 or "model" in " ".join(cells).lower():
            continue

        row = _build_row(
            config,
            {
                "model": cells[0],
                "provider": cells[1] if len(cells) > 1 else None,
                "country": cells[2] if len(cells) > 2 else None,
                "score": cells[3] if len(cells) > 3 else None,
                "cost": cells[4] if len(cells) > 4 else None,
            },
        )
        if row.model:
            rows.append(row)

    if not rows:
        logger.error(
            "HTML parsing yielded zero rows; upstream structure may have changed.",
            extra={"table": config.table_name, "url": config.page_url},
        )
    return rows


def extract_candidates_from_html(html: str) -> list[dict[str, Any]]:
    return _extract_json_candidates(html)
