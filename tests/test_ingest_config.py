from pathlib import Path

from directory.ingest import load_categories, load_entities

CONFIG_DIR = Path(__file__).parent.parent / "config"


def test_load_categories_has_expected_ids():
    categories = load_categories(CONFIG_DIR / "categories.yaml")
    ids = {c["category_id"] for c in categories}
    assert {"ai-crawler", "crawler-framework", "browser-agent", "research-agent", "agent-orchestration"} <= ids


def test_load_entities_have_required_fields():
    entities = load_entities(CONFIG_DIR / "entities.yaml")
    assert len(entities) >= 10
    for e in entities:
        assert e["canonical_name"]
        assert e["github_repo"]
        assert "/" in e["github_repo"]
        assert e["primary_category"]


def test_every_entity_primary_category_is_defined():
    categories = load_categories(CONFIG_DIR / "categories.yaml")
    category_ids = {c["category_id"] for c in categories}
    entities = load_entities(CONFIG_DIR / "entities.yaml")
    for e in entities:
        assert e["primary_category"] in category_ids
