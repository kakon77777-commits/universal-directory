import datetime as dt
import json
from pathlib import Path

from directory.cli import _build_all_languages
from directory.store import DirectoryStore, Evidence

NOW = dt.datetime(2026, 7, 20, tzinfo=dt.timezone.utc)


def _seeded_store(tmp_path: Path) -> DirectoryStore:
    store = DirectoryStore(tmp_path / "d.db")
    store.upsert_category(
        "ai-crawler", "AI Crawlers",
        "Crawling tools that use semantic models to understand pages, generate or "
        "repair extraction rules, or convert web pages into LLM-usable formats.",
        None, "profile_v1",
    )
    entity_id = store.upsert_entity(
        "Crawl4AI", "open_source_tool", "Local, self-hosted, LLM-friendly web crawler",
        "A crawler.", NOW.isoformat(),
        urls={"github": "https://github.com/unclecode/crawl4ai", "homepage": "https://github.com/unclecode/crawl4ai"},
    )
    store.link_entity_category(entity_id, "ai-crawler", "primary", 1.0)
    store.add_evidence(Evidence(
        entity_id=entity_id, field_name="stars", value_json=json.dumps(1000),
        source_url="https://api.github.com/repos/unclecode/crawl4ai", source_text=None,
        source_tier=1, fetched_at=NOW.isoformat(), confidence=0.99,
    ))
    return store


def test_build_all_languages_creates_en_at_root_and_zh_subdir(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())

    assert (site_dir / "index.html").exists()
    assert (site_dir / "zh" / "index.html").exists()
    assert (site_dir / "entities" / "crawl4ai" / "index.html").exists()
    assert (site_dir / "zh" / "entities" / "crawl4ai" / "index.html").exists()
    store.close()


def test_build_all_languages_translates_content_only_in_zh(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())

    en_html = (site_dir / "index.html").read_text(encoding="utf-8")
    zh_html = (site_dir / "zh" / "index.html").read_text(encoding="utf-8")

    assert "AI Crawlers" in en_html
    assert "Universal Dynamic Curated Directory" in en_html
    assert "AI 爬蟲" in zh_html
    assert "通用動態策展目錄" in zh_html
    store.close()


def test_build_all_languages_copies_matrix_select_and_worker(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())

    assert (site_dir / "matrix-select.js").exists()
    assert (site_dir / "matrix-select.css").exists()
    assert (site_dir / "_worker.js").exists()
    worker_src = (site_dir / "_worker.js").read_text(encoding="utf-8")
    assert "directory.evemiss.com" in worker_src
    store.close()


def test_build_all_languages_cleans_stray_files_on_rerun(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())
    (site_dir / "stray.txt").write_text("leftover", encoding="utf-8")
    (site_dir / "zh" / "stray.txt").write_text("leftover", encoding="utf-8")

    _build_all_languages(store, site_dir, NOW.isoformat())
    assert not (site_dir / "stray.txt").exists()
    assert not (site_dir / "zh" / "stray.txt").exists()
    store.close()
