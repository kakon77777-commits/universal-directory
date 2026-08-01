"""Deterministic, versioned scoring engine.

Per doc section 23: Agent 的工作是解釋排名，不是憑自然語言決定排名 — 真正分數
由版本化程式計算. No LLM involved. Signals are read from the evidence table
written by ingest.py (GitHub stars/pushed_at/license/archived).
"""

from __future__ import annotations

import datetime as dt
import json
import math
from dataclasses import dataclass

from .store import DirectoryStore

PROFILE_VERSION = "open_source_ai_tools_v1"

# Adoption-friendliness proxy, not a moral ranking of licenses: permissive
# licenses score higher because they're easier to embed in a downstream
# product without extra legal review (doc section 45: 授權治理).
_LICENSE_SCORE = {
    "MIT": 1.0,
    "Apache-2.0": 1.0,
    "BSD-2-Clause": 1.0,
    "BSD-3-Clause": 1.0,
    "ISC": 1.0,
    "MPL-2.0": 0.7,
    "LGPL-3.0": 0.6,
    "GPL-3.0": 0.5,
    "GPL-2.0": 0.5,
    "AGPL-3.0": 0.4,
    "Elastic-2.0": 0.5,
    "BSL-1.1": 0.5,
}
_DEFAULT_LICENSE_SCORE = 0.5

_ACTIVITY_HALF_LIFE_DAYS = 180.0  # F_i(t) = e^{-lambda*(t-t_i)}, doc section 36

W_ACTIVITY = 0.4
W_POPULARITY = 0.4
W_LICENSE = 0.2
ARCHIVED_PENALTY = 5.0


@dataclass
class ScoredEntity:
    entity_id: str
    canonical_name: str
    tagline: str | None
    score: float
    positive_factors: list[str]
    negative_factors: list[str]


def _activity_score(pushed_at_iso: str | None, now: dt.datetime) -> float:
    if not pushed_at_iso:
        return 0.0
    pushed_at = dt.datetime.fromisoformat(pushed_at_iso.replace("Z", "+00:00"))
    days = max(0.0, (now - pushed_at).total_seconds() / 86400.0)
    return math.exp(-math.log(2) * days / _ACTIVITY_HALF_LIFE_DAYS)


def _popularity_score(stars: int, max_stars_in_category: int) -> float:
    if max_stars_in_category <= 0:
        return 0.0
    return math.log1p(stars) / math.log1p(max_stars_in_category)


def _license_score(spdx_id: str | None) -> float:
    if not spdx_id:
        return _DEFAULT_LICENSE_SCORE
    return _LICENSE_SCORE.get(spdx_id, _DEFAULT_LICENSE_SCORE)


def _read_json_evidence(store: DirectoryStore, entity_id: str, field: str):
    row = store.latest_evidence_value(entity_id, field)
    if row is None:
        return None
    return json.loads(row["value_json"])


def score_category(
    store: DirectoryStore, category_id: str, now: dt.datetime | None = None
) -> list[ScoredEntity]:
    now = now or dt.datetime.now(dt.timezone.utc)
    entities = store.entities_in_category(category_id)

    raw = []
    for entity in entities:
        entity_id = entity["entity_id"]
        stars = _read_json_evidence(store, entity_id, "stars") or 0
        pushed_at = _read_json_evidence(store, entity_id, "pushed_at")
        license_spdx = _read_json_evidence(store, entity_id, "license")
        archived = bool(_read_json_evidence(store, entity_id, "archived") or False)
        raw.append((entity, stars, pushed_at, license_spdx, archived))

    max_stars = max((r[1] for r in raw), default=0)

    scored: list[ScoredEntity] = []
    for entity, stars, pushed_at, license_spdx, archived in raw:
        activity = _activity_score(pushed_at, now)
        popularity = _popularity_score(stars, max_stars)
        license_score = _license_score(license_spdx)

        weighted = W_ACTIVITY * activity + W_POPULARITY * popularity + W_LICENSE * license_score
        penalty = ARCHIVED_PENALTY if archived else 0.0
        final_score = max(0.0, min(10.0, weighted * 10.0 - penalty))

        positive: list[str] = []
        negative: list[str] = []
        if popularity >= 0.8:
            positive.append(f"{stars} GitHub stars (top of category)")
        if activity >= 0.7:
            positive.append("recently active")
        if license_score >= 1.0:
            positive.append(f"permissive license ({license_spdx})")
        if archived:
            negative.append("repository archived")
        if activity < 0.2:
            negative.append("no recent commits")
        if license_score <= 0.4:
            negative.append(f"restrictive/copyleft license ({license_spdx})")

        scored.append(
            ScoredEntity(
                entity_id=entity["entity_id"],
                canonical_name=entity["canonical_name"],
                tagline=entity["tagline"],
                score=round(final_score, 2),
                positive_factors=positive,
                negative_factors=negative,
            )
        )

    scored.sort(key=lambda s: s.score, reverse=True)
    return scored


def write_category_rankings(
    store: DirectoryStore, category_id: str, now_iso: str
) -> list[ScoredEntity]:
    scored = score_category(store, category_id)
    for rank, s in enumerate(scored, start=1):
        explanation = json.dumps(
            {"positive_factors": s.positive_factors, "negative_factors": s.negative_factors},
            ensure_ascii=False,
        )
        store.write_ranking(s.entity_id, category_id, s.score, rank, explanation, now_iso)
    return scored


def snapshot_period(store: DirectoryStore, granularity: str, period_key: str, now_iso: str) -> None:
    """Freezes this build's rankings into the historical archive at one
    granularity (doc section 70: 從目錄到觀測系統 — a directory that keeps
    history becomes a record of how a domain evolves). Call once per
    granularity per build (week/month/year — see cli.py) with each
    granularity's own period_key computed from the same now_iso.

    Independent of `write_category_rankings()`/`ranking_results` above
    (that pathway is unused by the live build — see sitegen.py, which
    reads `score_category()` directly): this computes scores itself so
    the archive doesn't depend on wiring up an unrelated, currently-dead
    table. Safe to call every build regardless of granularity —
    `write_archive_snapshot_row` upserts on (granularity, period_key,
    category_id, entity_id), so repeated calls within the same period
    just refresh it; a new period_key never touches a prior period's
    rows, which is what actually freezes them."""
    for cat in store.all_categories():
        scored = score_category(store, cat["category_id"])
        for rank, s in enumerate(scored, start=1):
            store.write_archive_snapshot_row(
                granularity=granularity,
                period_key=period_key,
                category_id=cat["category_id"],
                category_name=cat["name"],
                category_definition=cat["definition"],
                entity_id=s.entity_id,
                canonical_name=s.canonical_name,
                tagline=s.tagline,
                score=s.score,
                rank=rank,
                positive_factors_json=json.dumps(s.positive_factors, ensure_ascii=False),
                negative_factors_json=json.dumps(s.negative_factors, ensure_ascii=False),
                snapshotted_at=now_iso,
            )
