import datetime as dt
import json
from pathlib import Path

from directory.scoring import (
    _activity_score,
    _license_score,
    _popularity_score,
    score_category,
    write_category_rankings,
)
from directory.store import DirectoryStore, Evidence

NOW = dt.datetime(2026, 7, 19, tzinfo=dt.timezone.utc)


def test_activity_score_is_high_for_a_fresh_push():
    score = _activity_score(NOW.isoformat(), NOW)
    assert score > 0.99


def test_activity_score_halves_at_half_life():
    pushed = (NOW - dt.timedelta(days=180)).isoformat()
    score = _activity_score(pushed, NOW)
    assert 0.45 < score < 0.55


def test_activity_score_is_zero_when_missing():
    assert _activity_score(None, NOW) == 0.0


def test_popularity_score_zero_when_no_stars_in_category():
    assert _popularity_score(0, 0) == 0.0


def test_popularity_score_is_one_at_category_max():
    assert _popularity_score(500, 500) == 1.0


def test_popularity_score_orders_by_stars():
    low = _popularity_score(10, 1000)
    high = _popularity_score(500, 1000)
    assert 0 < low < high < 1.0


def test_license_score_permissive_vs_copyleft():
    assert _license_score("MIT") == 1.0
    assert _license_score("Apache-2.0") == 1.0
    assert _license_score("AGPL-3.0") < _license_score("MIT")


def test_license_score_defaults_for_unknown_or_missing():
    assert _license_score(None) == 0.5
    assert _license_score("SOME-UNKNOWN-LICENSE") == 0.5


def _seed_entity(store, name, stars, pushed_at, license_spdx, archived, category="ai-crawler"):
    entity_id = store.upsert_entity(name, "open_source_tool", "tagline", None, "t0")
    store.link_entity_category(entity_id, category, "primary", 1.0)
    for field, value in [
        ("stars", stars), ("pushed_at", pushed_at), ("license", license_spdx), ("archived", archived),
    ]:
        store.add_evidence(Evidence(
            entity_id=entity_id, field_name=field, value_json=json.dumps(value),
            source_url="https://api.github.com/repos/x", source_text=None,
            source_tier=1, fetched_at="t0", confidence=0.99,
        ))
    return entity_id


def test_score_category_ranks_healthy_project_above_archived_one(tmp_path: Path):
    store = DirectoryStore(tmp_path / "d.db")
    store.upsert_category("ai-crawler", "AI 爬蟲", "def", None, "profile_v1")

    healthy_id = _seed_entity(
        store, "Healthy", stars=1000, pushed_at=NOW.isoformat(), license_spdx="MIT", archived=False
    )
    stale_id = _seed_entity(
        store, "Stale", stars=50,
        pushed_at=(NOW - dt.timedelta(days=900)).isoformat(),
        license_spdx="AGPL-3.0", archived=True,
    )

    ranked = score_category(store, "ai-crawler", now=NOW)
    assert [e.entity_id for e in ranked] == [healthy_id, stale_id]
    assert ranked[0].score > ranked[1].score
    assert "repository archived" in ranked[1].negative_factors
    store.close()


def test_write_category_rankings_persists_rank_order(tmp_path: Path):
    store = DirectoryStore(tmp_path / "d.db")
    store.upsert_category("ai-crawler", "AI 爬蟲", "def", None, "profile_v1")
    _seed_entity(store, "Healthy", stars=1000, pushed_at=NOW.isoformat(), license_spdx="MIT", archived=False)
    _seed_entity(
        store, "Stale", stars=50, pushed_at=(NOW - dt.timedelta(days=900)).isoformat(),
        license_spdx="AGPL-3.0", archived=True,
    )

    write_category_rankings(store, "ai-crawler", now_iso=NOW.isoformat())
    rankings = store.rankings_for_category("ai-crawler")
    assert [r["canonical_name"] for r in rankings] == ["Healthy", "Stale"]
    assert rankings[0]["rank"] == 1
    assert rankings[1]["rank"] == 2
    store.close()
