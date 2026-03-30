from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urljoin
from urllib.request import urlopen

HF_BASE_URL = "https://huggingface.co"
MODELS_TRENDING_URL = f"{HF_BASE_URL}/models?sort=trending"
DATASETS_TRENDING_URL = f"{HF_BASE_URL}/datasets?sort=trending"
CACHE_PATH = Path("cache/hf_trending_latest.json")


@dataclass
class TrendingItem:
    rank: int
    name: str
    task_or_tag: str
    likes_or_score: int | float | str
    updated_at: str
    url: str
    captured_at: str


class _CardParser(HTMLParser):
    def __init__(self, item_type: str):
        super().__init__()
        self.item_type = item_type
        self.cards: list[dict] = []
        self._in_article = False
        self._depth = 0
        self._current: dict | None = None
        self._capture_name = False
        self._capture_time = False
        self._capture_tag = False

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        cls = attrs_d.get("class", "")

        if tag == "article" and "overview-card-wrapper" in cls:
            self._in_article = True
            self._depth = 1
            self._current = {
                "href": "",
                "name": "",
                "task_or_tag": "",
                "updated_at": "",
                "text": "",
            }
            return

        if self._in_article:
            self._depth += 1
            if tag == "a":
                href = attrs_d.get("href", "")
                if href.startswith(f"/{self.item_type}/") and self._current and not self._current["href"]:
                    self._current["href"] = href
            elif tag in {"h3", "h4"}:
                self._capture_name = True
            elif tag == "time":
                self._capture_time = True
                if self._current:
                    self._current["updated_at"] = attrs_d.get("datetime", "")
            elif tag in {"span", "div"} and ("text-gray-500" in cls or "tag" in cls):
                self._capture_tag = True

    def handle_endtag(self, tag):
        if self._in_article:
            if tag in {"h3", "h4"}:
                self._capture_name = False
            elif tag == "time":
                self._capture_time = False
            elif tag in {"span", "div"}:
                self._capture_tag = False

            self._depth -= 1
            if self._depth <= 0:
                if self._current:
                    self.cards.append(self._current)
                self._current = None
                self._in_article = False

    def handle_data(self, data):
        if not self._in_article or not self._current:
            return
        text = data.strip()
        if not text:
            return

        self._current["text"] += f" {text}"
        if self._capture_name and not self._current["name"]:
            self._current["name"] = text
        elif self._capture_tag and not self._current["task_or_tag"]:
            self._current["task_or_tag"] = text
        elif self._capture_time and not self._current["updated_at"]:
            self._current["updated_at"] = text


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(text: str) -> int | str:
    cleaned = text.replace(",", "").strip()
    return int(cleaned) if cleaned.isdigit() else text.strip()


def _default_fetcher(url: str) -> tuple[int, str]:
    with urlopen(url, timeout=12) as resp:  # nosec B310
        return resp.getcode() or 200, resp.read().decode("utf-8", errors="ignore")


def _parse_cards(html: str, item_type: str, limit: int) -> list[TrendingItem]:
    parser = _CardParser(item_type=item_type)
    parser.feed(html)

    items: list[TrendingItem] = []
    captured_at = _now_iso()

    for idx, card in enumerate(parser.cards, start=1):
        href = card.get("href", "")
        if not href:
            continue
        url = urljoin(HF_BASE_URL, href)
        name = card.get("name") or href.strip("/").split("/")[-1]

        likes_or_score: int | str = ""
        m = re.search(r"(\d+[\d,]*)\s*(likes|downloads|score)", card.get("text", ""), flags=re.I)
        if m:
            likes_or_score = _safe_int(m.group(1))

        items.append(
            TrendingItem(
                rank=idx,
                name=name,
                task_or_tag=card.get("task_or_tag", ""),
                likes_or_score=likes_or_score,
                updated_at=card.get("updated_at", ""),
                url=url,
                captured_at=captured_at,
            )
        )
        if len(items) >= limit:
            break

    return items


def _dedupe_and_re_rank(items: Iterable[TrendingItem], limit: int) -> list[TrendingItem]:
    deduped: list[TrendingItem] = []
    seen = set()

    for item in sorted(items, key=lambda x: x.rank):
        key = item.url or item.name
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    for idx, item in enumerate(deduped[:limit], start=1):
        item.rank = idx

    return deduped[:limit]


def _save_cache(payload: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_cache() -> dict | None:
    if not CACHE_PATH.exists():
        return None
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def fetch_trending(
    limit: int = 10,
    fetcher: Callable[[str], tuple[int, str]] | None = None,
) -> dict:
    fetcher = fetcher or _default_fetcher
    captured_at = _now_iso()

    try:
        model_status, model_html = fetcher(MODELS_TRENDING_URL)
        dataset_status, dataset_html = fetcher(DATASETS_TRENDING_URL)
        if model_status >= 400 or dataset_status >= 400:
            raise ValueError("Upstream HTTP error")

        models = _parse_cards(model_html, "models", limit)
        datasets = _parse_cards(dataset_html, "datasets", limit)
        if not models or not datasets:
            raise ValueError("Trending page structure may have changed")

        payload = {
            "top_models": [asdict(i) for i in _dedupe_and_re_rank(models, limit)],
            "top_datasets": [asdict(i) for i in _dedupe_and_re_rank(datasets, limit)],
            "captured_at": captured_at,
            "stale": False,
        }
        _save_cache(payload)
        return payload
    except Exception:
        cached = _load_cache()
        if cached:
            cached["stale"] = True
            return cached
        return {
            "top_models": [],
            "top_datasets": [],
            "captured_at": captured_at,
            "stale": True,
        }
