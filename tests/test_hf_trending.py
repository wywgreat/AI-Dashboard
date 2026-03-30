from __future__ import annotations

from pathlib import Path

from collectors.huggingface import trending


def test_dedupe_and_rank_sorted():
    html = """
    <html><body>
      <article class='overview-card-wrapper'>
        <a href='/models/a'></a><h4>model-a</h4><span class='text-gray-500'>text-classification</span><time datetime='2026-01-01'></time>
      </article>
      <article class='overview-card-wrapper'>
        <a href='/models/a'></a><h4>model-a-dup</h4><span class='text-gray-500'>text-classification</span><time datetime='2026-01-01'></time>
      </article>
      <article class='overview-card-wrapper'>
        <a href='/models/b'></a><h4>model-b</h4><span class='text-gray-500'>summarization</span><time datetime='2026-01-02'></time>
      </article>
    </body></html>
    """

    items = trending._parse_cards(html, "models", limit=10)
    out = trending._dedupe_and_re_rank(items, limit=10)

    assert len(out) == 2
    assert [x.rank for x in out] == [1, 2]
    assert out[0].url.endswith("/models/a")
    assert out[1].url.endswith("/models/b")


def test_fallback_to_cache_when_structure_changed(tmp_path: Path, monkeypatch):
    cache_file = tmp_path / "hf_trending_latest.json"
    monkeypatch.setattr(trending, "CACHE_PATH", cache_file)

    cache_file.write_text(
        '{"top_models":[{"rank":1,"name":"m1","task_or_tag":"","likes_or_score":"","updated_at":"","url":"u","captured_at":"t"}],"top_datasets":[],"captured_at":"t","stale":false}',
        encoding="utf-8",
    )

    def bad_fetcher(_url: str):
        return 200, "<html>broken</html>"

    data = trending.fetch_trending(limit=10, fetcher=bad_fetcher)
    assert data["stale"] is True
    assert data["top_models"][0]["name"] == "m1"
