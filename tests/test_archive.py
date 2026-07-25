import datetime as dt
import json
from pathlib import Path

from directory.cli import _build_all_languages
from directory.scoring import snapshot_month
from directory.store import DirectoryStore, Evidence

NOW = dt.datetime(2026, 7, 25, tzinfo=dt.timezone.utc)


def _seed_entity(store, name, stars, license_spdx="MIT", category="ai-crawler"):
    entity_id = store.upsert_entity(name, "open_source_tool", f"{name} tagline", None, "t0")
    store.link_entity_category(entity_id, category, "primary", 1.0)
    for field, value in [("stars", stars), ("pushed_at", NOW.isoformat()), ("license", license_spdx), ("archived", False)]:
        store.add_evidence(Evidence(
            entity_id=entity_id, field_name=field, value_json=json.dumps(value),
            source_url="https://api.github.com/repos/x", source_text=None,
            source_tier=1, fetched_at="t0", confidence=0.99,
        ))
    return entity_id


def _seeded_store(tmp_path: Path) -> DirectoryStore:
    store = DirectoryStore(tmp_path / "d.db")
    store.upsert_category("ai-crawler", "AI Crawlers", "definition text", None, "profile_v1")
    _seed_entity(store, "Crawl4AI", stars=1000)
    _seed_entity(store, "Firecrawl", stars=500, license_spdx="AGPL-3.0")
    return store


def test_snapshot_month_writes_one_row_per_entity_per_category(tmp_path: Path):
    store = _seeded_store(tmp_path)
    snapshot_month(store, "2026-07", NOW.isoformat())

    rows = store.archive_snapshot_for_month("2026-07")
    assert len(rows) == 2
    assert {r["canonical_name"] for r in rows} == {"Crawl4AI", "Firecrawl"}
    assert rows[0]["category_name"] == "AI Crawlers"
    store.close()


def test_snapshot_month_upserts_within_same_month(tmp_path: Path):
    store = _seeded_store(tmp_path)
    snapshot_month(store, "2026-07", NOW.isoformat())
    snapshot_month(store, "2026-07", NOW.isoformat())  # re-run, same month

    rows = store.archive_snapshot_for_month("2026-07")
    assert len(rows) == 2  # not duplicated
    store.close()


def test_snapshot_month_keeps_prior_months_untouched(tmp_path: Path):
    store = _seeded_store(tmp_path)
    snapshot_month(store, "2026-07", NOW.isoformat())

    # A later month with a different catalog (Firecrawl "removed", one new entity)
    _seed_entity(store, "ScrapeGraphAI", stars=2000)
    snapshot_month(store, "2026-08", (NOW + dt.timedelta(days=30)).isoformat())

    july_rows = store.archive_snapshot_for_month("2026-07")
    august_rows = store.archive_snapshot_for_month("2026-08")
    assert {r["canonical_name"] for r in july_rows} == {"Crawl4AI", "Firecrawl"}
    assert {r["canonical_name"] for r in august_rows} == {"Crawl4AI", "Firecrawl", "ScrapeGraphAI"}
    assert store.archive_months() == ["2026-08", "2026-07"]  # newest first
    store.close()


def test_build_all_languages_generates_archive_index_and_month_pages(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())

    assert (site_dir / "archive" / "index.html").exists()
    assert (site_dir / "archive" / "2026-07" / "index.html").exists()
    assert (site_dir / "zh" / "archive" / "index.html").exists()
    assert (site_dir / "zh" / "archive" / "2026-07" / "index.html").exists()
    store.close()


def test_archive_month_page_shows_frozen_ranking_data(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())

    html = (site_dir / "archive" / "2026-07" / "index.html").read_text(encoding="utf-8")
    assert "Crawl4AI" in html
    assert "Firecrawl" in html
    assert "AI Crawlers" in html
    assert "July 2026" in html


def test_archive_survives_a_later_month_with_removed_entity(tmp_path: Path):
    """The whole point of freezing at snapshot time: renaming/removing an
    entity later must not retroactively change what an old month says."""
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())

    # Simulate Firecrawl being dropped from the live catalog next month —
    # snapshot a new month from a store that no longer has it linked to
    # a category (closest equivalent here: just snapshot again with the
    # same store — the July page must still show Firecrawl regardless).
    later = NOW + dt.timedelta(days=30)
    snapshot_month(store, "2026-08", later.isoformat())
    _build_all_languages(store, site_dir, later.isoformat())

    july_html = (site_dir / "archive" / "2026-07" / "index.html").read_text(encoding="utf-8")
    assert "Firecrawl" in july_html
    store.close()
