import datetime as dt
import json
from pathlib import Path

from directory.sitegen import build_site, slugify
from directory.store import DirectoryStore, Evidence

NOW = dt.datetime(2026, 7, 19, tzinfo=dt.timezone.utc)


def test_slugify_basic():
    assert slugify("Crawl4AI") == "crawl4ai"
    assert slugify("Kortix/Suna") == "kortix-suna"
    assert slugify("  Weird   Name!! ") == "weird-name"


def _seeded_store(tmp_path: Path) -> DirectoryStore:
    store = DirectoryStore(tmp_path / "d.db")
    store.upsert_category("ai-crawler", "AI 爬蟲", "definition text", None, "profile_v1")
    entity_id = store.upsert_entity(
        "Crawl4AI", "open_source_tool", "本地、自架、LLM-Friendly Web Crawler",
        "A crawler.", NOW.isoformat(),
        urls={"github": "https://github.com/unclecode/crawl4ai", "homepage": "https://github.com/unclecode/crawl4ai"},
    )
    store.link_entity_category(entity_id, "ai-crawler", "primary", 1.0)
    for field, value, tier in [
        ("stars", 1000, 1), ("pushed_at", NOW.isoformat(), 1),
        ("license", "Apache-2.0", 1), ("archived", False, 1),
        ("topics", ["crawler", "ai"], 1),
    ]:
        store.add_evidence(Evidence(
            entity_id=entity_id, field_name=field, value_json=json.dumps(value),
            source_url="https://api.github.com/repos/unclecode/crawl4ai", source_text=None,
            source_tier=tier, fetched_at=NOW.isoformat(), confidence=0.99,
        ))
    return store


def test_build_site_creates_expected_pages(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    build_site(store, site_dir, NOW.isoformat())

    assert (site_dir / "index.html").exists()
    assert (site_dir / "categories" / "ai-crawler" / "index.html").exists()
    assert (site_dir / "entities" / "crawl4ai" / "index.html").exists()
    store.close()


def test_build_site_index_lists_entity_and_score(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    build_site(store, site_dir, NOW.isoformat())

    index_html = (site_dir / "index.html").read_text(encoding="utf-8")
    assert "Crawl4AI" in index_html
    assert "AI 爬蟲" in index_html
    store.close()


def test_build_site_entity_page_shows_evidence_source(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    build_site(store, site_dir, NOW.isoformat())

    entity_html = (site_dir / "entities" / "crawl4ai" / "index.html").read_text(encoding="utf-8")
    assert "api.github.com/repos/unclecode/crawl4ai" in entity_html
    assert "Apache-2.0" in entity_html
    store.close()


def test_build_site_does_not_clean_output_dir_itself(tmp_path: Path):
    """build_site() no longer owns cleaning the output tree — a caller
    building multiple languages into sibling directories under one site
    root must only clean that root once (see cli.py's
    _build_all_languages), not per-language build_site() call, or an
    en-then-zh build would wipe the zh/ subdir the moment the en pass
    (targeting the same root) ran. Cleanliness across a full multi-language
    build is exercised in test_cli.py instead."""
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    build_site(store, site_dir, NOW.isoformat())
    (site_dir / "stray.txt").write_text("not cleaned by build_site() itself", encoding="utf-8")

    build_site(store, site_dir, NOW.isoformat())
    assert (site_dir / "stray.txt").exists()
    store.close()
