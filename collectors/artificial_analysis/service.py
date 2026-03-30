from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .cache import AACache
from .parser import TABLES, extract_candidates_from_html, parse_from_html, parse_from_json_payload
from .schemas import AAResponse

logger = logging.getLogger(__name__)

XHR_PATTERN = re.compile(r"(?:fetch\(|axios\.|d3\.json\(|XMLHttpRequest).*?['\"]([^'\"]+\.json[^'\"]*)['\"]")


class AACollectorService:
    def __init__(self, cache: AACache | None = None, timeout: int = 20) -> None:
        self.cache = cache or AACache()
        self.timeout = timeout

    def _download(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _probe_xhr_json(self, page_url: str, html: str) -> list[dict]:
        discovered = {urljoin(page_url, m) for m in XHR_PATTERN.findall(html)}
        payloads: list[dict] = []
        for url in discovered:
            try:
                text = self._download(url)
                payload = json.loads(text)
                if isinstance(payload, dict):
                    payloads.append(payload)
                elif isinstance(payload, list):
                    payloads.append({"items": payload})
            except Exception as exc:
                logger.warning("Failed probing XHR JSON endpoint", extra={"url": url, "error": str(exc)})
        return payloads

    def collect(self, table_slug: str) -> AAResponse:
        if table_slug not in TABLES:
            raise ValueError(f"Unsupported table slug: {table_slug}")

        cache_key = f"aa:{table_slug}"
        cached = self.cache.get(cache_key)
        if cached:
            return AAResponse.model_validate({**cached, "from_cache": True})

        cfg = TABLES[table_slug]

        try:
            html = self._download(cfg.page_url)
        except (HTTPError, URLError) as exc:
            logger.error("Failed to download source page", extra={"url": cfg.page_url, "error": str(exc)})
            raise

        embedded_payloads = extract_candidates_from_html(html)
        xhr_payloads = self._probe_xhr_json(cfg.page_url, html)
        all_payloads = embedded_payloads + xhr_payloads

        rows = parse_from_json_payload(cfg, all_payloads) if all_payloads else []
        if not rows:
            logger.warning(
                "No directly consumable JSON/XHR data found. Falling back to HTML table parsing.",
                extra={"table": cfg.table_name, "url": cfg.page_url},
            )
            rows = parse_from_html(cfg, html)

        if not rows:
            logger.error(
                "Collector produced zero rows after all parsing paths.",
                extra={"table": cfg.table_name, "url": cfg.page_url},
            )

        now = datetime.now(timezone.utc)
        response = AAResponse(
            source="artificialanalysis.ai",
            table=cfg.table_name,
            captured_at=now,
            rows=rows,
            from_cache=False,
        )
        self.cache.set(cache_key, response.model_dump(mode="json"))
        return response
