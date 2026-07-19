from pathlib import Path

from directory.store import DirectoryStore, Evidence


def test_upsert_entity_creates_stable_id(tmp_path: Path):
    store = DirectoryStore(tmp_path / "d.db")
    id1 = store.upsert_entity("Crawl4AI", "open_source_tool", "tagline", None, "t0")
    id2 = store.upsert_entity("Crawl4AI", "open_source_tool", "tagline v2", None, "t1")
    assert id1 == id2
    store.close()


def test_upsert_entity_preserves_created_at_on_update(tmp_path: Path):
    store = DirectoryStore(tmp_path / "d.db")
    store.upsert_entity("Crawl4AI", "open_source_tool", "a", None, "t0")
    store.upsert_entity("Crawl4AI", "open_source_tool", "b", None, "t1")

    rows = store.all_entities()
    assert len(rows) == 1
    assert rows[0]["created_at"] == "t0"
    assert rows[0]["updated_at"] == "t1"
    assert rows[0]["tagline"] == "b"
    store.close()


def test_entity_urls_roundtrip(tmp_path: Path):
    store = DirectoryStore(tmp_path / "d.db")
    entity_id = store.upsert_entity(
        "Crawl4AI", "open_source_tool", "t", None, "t0",
        urls={"github": "https://github.com/unclecode/crawl4ai", "homepage": "https://example.com"},
    )
    urls = store.entity_urls(entity_id)
    assert urls == {
        "github": "https://github.com/unclecode/crawl4ai",
        "homepage": "https://example.com",
    }
    store.close()


def test_category_and_entity_linking(tmp_path: Path):
    store = DirectoryStore(tmp_path / "d.db")
    store.upsert_category("ai-crawler", "AI 爬蟲", "definition", None, "profile_v1")
    entity_id = store.upsert_entity("Crawl4AI", "open_source_tool", "t", None, "t0")
    store.link_entity_category(entity_id, "ai-crawler", "primary", 1.0)

    entities = store.entities_in_category("ai-crawler")
    assert len(entities) == 1
    assert entities[0]["canonical_name"] == "Crawl4AI"

    cats = store.categories_for_entity(entity_id)
    assert len(cats) == 1
    assert cats[0]["category_id"] == "ai-crawler"
    store.close()


def test_add_evidence_and_latest_evidence_value_prefers_lowest_tier(tmp_path: Path):
    store = DirectoryStore(tmp_path / "d.db")
    entity_id = store.upsert_entity("Crawl4AI", "open_source_tool", "t", None, "t0")

    store.add_evidence(Evidence(
        entity_id=entity_id, field_name="stars", value_json="100",
        source_url="https://example.com/scraped", source_text=None,
        source_tier=2, fetched_at="t0", confidence=0.9,
    ))
    store.add_evidence(Evidence(
        entity_id=entity_id, field_name="stars", value_json="120",
        source_url="https://api.github.com/repos/x", source_text=None,
        source_tier=1, fetched_at="t0", confidence=0.99,
    ))

    latest = store.latest_evidence_value(entity_id, "stars")
    assert latest["source_tier"] == 1
    assert latest["value_json"] == "120"
    store.close()


def test_write_ranking_and_read_back(tmp_path: Path):
    store = DirectoryStore(tmp_path / "d.db")
    store.upsert_category("ai-crawler", "AI 爬蟲", "definition", None, "profile_v1")
    entity_id = store.upsert_entity("Crawl4AI", "open_source_tool", "t", None, "t0")
    store.link_entity_category(entity_id, "ai-crawler", "primary", 1.0)

    store.write_ranking(entity_id, "ai-crawler", 8.8, 1, '{"positive_factors": []}', "t0")
    rankings = store.rankings_for_category("ai-crawler")
    assert len(rankings) == 1
    assert rankings[0]["score"] == 8.8
    assert rankings[0]["canonical_name"] == "Crawl4AI"
    store.close()
