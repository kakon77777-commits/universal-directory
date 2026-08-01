import datetime as dt
import json
from pathlib import Path

from directory.cli import _build_all_languages, _period_keys
from directory.scoring import snapshot_period
from directory.store import DirectoryStore, Evidence

NOW = dt.datetime(2026, 7, 25, tzinfo=dt.timezone.utc)  # Saturday, ISO week 30


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


def test_period_keys_derives_iso_week_month_year():
    keys = _period_keys(NOW.isoformat())
    assert keys == {"week": "2026-W30", "month": "2026-07", "year": "2026"}


def test_period_keys_sunday_falls_in_the_week_it_closes():
    # 2026-08-02 is a Sunday — Neo's own update cadence ("每周日更新").
    # ISO weeks run Mon-Sun, so a Sunday build's date is always the last
    # day of the week it's snapshotting, no special-casing needed.
    sunday = dt.datetime(2026, 8, 2, tzinfo=dt.timezone.utc)
    keys = _period_keys(sunday.isoformat())
    assert keys["week"] == "2026-W31"


def test_snapshot_period_writes_one_row_per_entity_per_category(tmp_path: Path):
    store = _seeded_store(tmp_path)
    snapshot_period(store, "month", "2026-07", NOW.isoformat())

    rows = store.archive_snapshot_for_period("month", "2026-07")
    assert len(rows) == 2
    assert {r["canonical_name"] for r in rows} == {"Crawl4AI", "Firecrawl"}
    assert rows[0]["category_name"] == "AI Crawlers"
    store.close()


def test_snapshot_period_upserts_within_same_period(tmp_path: Path):
    store = _seeded_store(tmp_path)
    snapshot_period(store, "week", "2026-W30", NOW.isoformat())
    snapshot_period(store, "week", "2026-W30", NOW.isoformat())  # re-run, same week

    rows = store.archive_snapshot_for_period("week", "2026-W30")
    assert len(rows) == 2  # not duplicated
    store.close()


def test_snapshot_period_keeps_prior_periods_untouched(tmp_path: Path):
    store = _seeded_store(tmp_path)
    snapshot_period(store, "month", "2026-07", NOW.isoformat())

    _seed_entity(store, "ScrapeGraphAI", stars=2000)
    snapshot_period(store, "month", "2026-08", (NOW + dt.timedelta(days=30)).isoformat())

    july_rows = store.archive_snapshot_for_period("month", "2026-07")
    august_rows = store.archive_snapshot_for_period("month", "2026-08")
    assert {r["canonical_name"] for r in july_rows} == {"Crawl4AI", "Firecrawl"}
    assert {r["canonical_name"] for r in august_rows} == {"Crawl4AI", "Firecrawl", "ScrapeGraphAI"}
    assert store.archive_periods("month") == ["2026-08", "2026-07"]  # newest first
    store.close()


def test_snapshot_period_granularities_are_independent(tmp_path: Path):
    """Writing a week snapshot must not create/affect month or year rows
    for the same underlying data, and vice versa — they're only related
    by both being computed from the same score_category() call."""
    store = _seeded_store(tmp_path)
    snapshot_period(store, "week", "2026-W30", NOW.isoformat())

    assert store.archive_periods("week") == ["2026-W30"]
    assert store.archive_periods("month") == []
    assert store.archive_periods("year") == []
    store.close()


def test_build_all_languages_generates_all_three_granularities(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())

    assert (site_dir / "archive" / "index.html").exists()
    assert (site_dir / "archive" / "week" / "2026-W30" / "index.html").exists()
    assert (site_dir / "archive" / "month" / "2026-07" / "index.html").exists()
    assert (site_dir / "archive" / "year" / "2026" / "index.html").exists()
    assert (site_dir / "zh" / "archive" / "week" / "2026-W30" / "index.html").exists()
    store.close()


def test_archive_period_page_shows_frozen_ranking_data(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())

    month_html = (site_dir / "archive" / "month" / "2026-07" / "index.html").read_text(encoding="utf-8")
    assert "Crawl4AI" in month_html
    assert "Firecrawl" in month_html
    assert "AI Crawlers" in month_html
    assert "July 2026" in month_html

    week_html = (site_dir / "archive" / "week" / "2026-W30" / "index.html").read_text(encoding="utf-8")
    assert "Week 30, 2026" in week_html

    year_html = (site_dir / "archive" / "year" / "2026" / "index.html").read_text(encoding="utf-8")
    assert "2026" in year_html


def test_archive_index_lists_periods_under_each_granularity_heading(tmp_path: Path):
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())

    index_html = (site_dir / "archive" / "index.html").read_text(encoding="utf-8")
    assert "By Week" in index_html
    assert "By Month" in index_html
    assert "By Year" in index_html
    assert 'href="/archive/week/2026-W30/"' in index_html
    assert 'href="/archive/month/2026-07/"' in index_html
    assert 'href="/archive/year/2026/"' in index_html
    store.close()


def test_archive_survives_a_later_period_with_removed_entity(tmp_path: Path):
    """The whole point of freezing at snapshot time: renaming/removing an
    entity later must not retroactively change what an old period says."""
    store = _seeded_store(tmp_path)
    site_dir = tmp_path / "site"
    _build_all_languages(store, site_dir, NOW.isoformat())

    later = NOW + dt.timedelta(days=30)
    snapshot_period(store, "month", "2026-08", later.isoformat())
    _build_all_languages(store, site_dir, later.isoformat())

    july_html = (site_dir / "archive" / "month" / "2026-07" / "index.html").read_text(encoding="utf-8")
    assert "Firecrawl" in july_html
    store.close()


def test_store_migrates_pre_granularity_archive_table(tmp_path: Path):
    """A DB created before the week/month/year generalization has
    archive_snapshots keyed on a bare `month_key` column with no
    `granularity` — opening it must migrate those rows forward as
    granularity='month', not silently lose them."""
    db_path = tmp_path / "old.db"
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE archive_snapshots (
            month_key TEXT NOT NULL,
            category_id TEXT NOT NULL,
            category_name TEXT NOT NULL,
            category_definition TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            tagline TEXT,
            score REAL NOT NULL,
            rank INTEGER NOT NULL,
            positive_factors_json TEXT NOT NULL,
            negative_factors_json TEXT NOT NULL,
            snapshotted_at TEXT NOT NULL,
            PRIMARY KEY (month_key, category_id, entity_id)
        );
        """
    )
    conn.execute(
        "INSERT INTO archive_snapshots VALUES ('2026-07', 'ai-crawler', 'AI Crawlers', 'def', "
        "'ent1', 'Crawl4AI', 'tag', 9.5, 1, '[]', '[]', 't0')"
    )
    conn.commit()
    conn.close()

    store = DirectoryStore(db_path)
    rows = store.archive_snapshot_for_period("month", "2026-07")
    assert len(rows) == 1
    assert rows[0]["canonical_name"] == "Crawl4AI"
    assert store.archive_periods("month") == ["2026-07"]
    store.close()
