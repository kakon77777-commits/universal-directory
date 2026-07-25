"""SQLite store for entities/categories/evidence/rankings.

Schema is a scoped-down version of the entity model in
通用動態策展目錄_Agent自動治理平台_技術白皮書 (section 38): entities,
entity_aliases, entity_urls, categories, entity_categories, evidence,
ranking_results.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCORE_PROFILE_VERSION = "score_profile_v1"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    tagline TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entity_aliases (
    alias_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE IF NOT EXISTS entity_urls (
    entity_id TEXT NOT NULL,
    url_type TEXT NOT NULL,
    url TEXT NOT NULL,
    PRIMARY KEY (entity_id, url_type)
);

CREATE TABLE IF NOT EXISTS categories (
    category_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    definition TEXT NOT NULL,
    parent_id TEXT,
    ranking_profile TEXT
);

CREATE TABLE IF NOT EXISTS entity_categories (
    entity_id TEXT NOT NULL,
    category_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    confidence REAL,
    PRIMARY KEY (entity_id, category_id)
);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    value_json TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_text TEXT,
    source_tier INTEGER NOT NULL,
    fetched_at TEXT NOT NULL,
    confidence REAL NOT NULL,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE IF NOT EXISTS ranking_results (
    ranking_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    category_id TEXT NOT NULL,
    score REAL NOT NULL,
    rank INTEGER NOT NULL,
    profile_version TEXT NOT NULL,
    explanation_json TEXT,
    calculated_at TEXT NOT NULL
);

-- Monthly historical archive (doc section 10/70: 版本歷史/從目錄到觀測系統 —
-- a directory that keeps its own history becomes a record of how a domain
-- evolves, not just its current state). Keyed by (month_key, category_id,
-- entity_id) so re-snapshotting the SAME month (repeated builds within
-- that month) upserts in place, while a NEW month_key just adds new rows
-- without ever touching a past month's — the archive freezes itself
-- naturally at each calendar month boundary, no separate "already
-- snapshotted this month" bookkeeping needed. category_name/definition are
-- denormalized (copied at snapshot time, not joined live) so a later
-- rename/removal of a category in categories.yaml can't retroactively
-- change what an old snapshot says it was.
CREATE TABLE IF NOT EXISTS archive_snapshots (
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


def _id_for(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


@dataclass
class Entity:
    entity_id: str
    canonical_name: str
    entity_type: str
    tagline: str | None
    description: str | None
    status: str


@dataclass
class Evidence:
    entity_id: str
    field_name: str
    value_json: str
    source_url: str
    source_text: str | None
    source_tier: int
    fetched_at: str
    confidence: float


class DirectoryStore:
    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- entities ----------------------------------------------------------

    def upsert_entity(
        self,
        canonical_name: str,
        entity_type: str,
        tagline: str | None,
        description: str | None,
        now: str,
        aliases: list[str] | None = None,
        urls: dict[str, str] | None = None,
    ) -> str:
        entity_id = _id_for("entity", canonical_name)
        existing = self._conn.execute(
            "SELECT created_at FROM entities WHERE entity_id = ?", (entity_id,)
        ).fetchone()
        created_at = existing[0] if existing else now

        self._conn.execute(
            """
            INSERT INTO entities (entity_id, canonical_name, entity_type, tagline, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                tagline=excluded.tagline,
                description=excluded.description,
                updated_at=excluded.updated_at
            """,
            (entity_id, canonical_name, entity_type, tagline, description, created_at, now),
        )

        for alias in aliases or []:
            alias_id = _id_for("alias", entity_id, alias)
            self._conn.execute(
                "INSERT OR IGNORE INTO entity_aliases (alias_id, entity_id, alias) VALUES (?, ?, ?)",
                (alias_id, entity_id, alias),
            )

        for url_type, url in (urls or {}).items():
            self._conn.execute(
                "INSERT INTO entity_urls (entity_id, url_type, url) VALUES (?, ?, ?) "
                "ON CONFLICT(entity_id, url_type) DO UPDATE SET url=excluded.url",
                (entity_id, url_type, url),
            )

        self._conn.commit()
        return entity_id

    def entity_urls(self, entity_id: str) -> dict[str, str]:
        cur = self._conn.execute(
            "SELECT url_type, url FROM entity_urls WHERE entity_id = ?", (entity_id,)
        )
        return dict(cur.fetchall())

    def all_entities(self) -> list[sqlite3.Row]:
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute("SELECT * FROM entities ORDER BY canonical_name ASC")
        return cur.fetchall()

    # -- categories ----------------------------------------------------------

    def upsert_category(
        self, category_id: str, name: str, definition: str, parent_id: str | None, ranking_profile: str
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO categories (category_id, name, definition, parent_id, ranking_profile)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(category_id) DO UPDATE SET
                name=excluded.name, definition=excluded.definition,
                parent_id=excluded.parent_id, ranking_profile=excluded.ranking_profile
            """,
            (category_id, name, definition, parent_id, ranking_profile),
        )
        self._conn.commit()

    def link_entity_category(
        self, entity_id: str, category_id: str, relation_type: str, confidence: float
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO entity_categories (entity_id, category_id, relation_type, confidence)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(entity_id, category_id) DO UPDATE SET
                relation_type=excluded.relation_type, confidence=excluded.confidence
            """,
            (entity_id, category_id, relation_type, confidence),
        )
        self._conn.commit()

    def all_categories(self) -> list[sqlite3.Row]:
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute("SELECT * FROM categories ORDER BY name ASC")
        return cur.fetchall()

    def entities_in_category(self, category_id: str) -> list[sqlite3.Row]:
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute(
            """
            SELECT e.* FROM entities e
            JOIN entity_categories ec ON ec.entity_id = e.entity_id
            WHERE ec.category_id = ?
            ORDER BY e.canonical_name ASC
            """,
            (category_id,),
        )
        return cur.fetchall()

    def categories_for_entity(self, entity_id: str) -> list[sqlite3.Row]:
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute(
            """
            SELECT c.* FROM categories c
            JOIN entity_categories ec ON ec.category_id = c.category_id
            WHERE ec.entity_id = ?
            ORDER BY c.name ASC
            """,
            (entity_id,),
        )
        return cur.fetchall()

    # -- evidence ------------------------------------------------------------

    def add_evidence(self, evidence: Evidence) -> None:
        evidence_id = _id_for(
            "evidence", evidence.entity_id, evidence.field_name, evidence.source_url
        )
        self._conn.execute(
            """
            INSERT INTO evidence (
                evidence_id, entity_id, field_name, value_json, source_url,
                source_text, source_tier, fetched_at, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                value_json=excluded.value_json,
                source_text=excluded.source_text,
                fetched_at=excluded.fetched_at,
                confidence=excluded.confidence
            """,
            (
                evidence_id, evidence.entity_id, evidence.field_name, evidence.value_json,
                evidence.source_url, evidence.source_text, evidence.source_tier,
                evidence.fetched_at, evidence.confidence,
            ),
        )
        self._conn.commit()

    def evidence_for_entity(self, entity_id: str) -> list[sqlite3.Row]:
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute(
            "SELECT * FROM evidence WHERE entity_id = ? ORDER BY field_name ASC", (entity_id,)
        )
        return cur.fetchall()

    def latest_evidence_value(self, entity_id: str, field_name: str) -> sqlite3.Row | None:
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute(
            """
            SELECT * FROM evidence WHERE entity_id = ? AND field_name = ?
            ORDER BY source_tier ASC, fetched_at DESC LIMIT 1
            """,
            (entity_id, field_name),
        )
        return cur.fetchone()

    # -- ranking ---------------------------------------------------------

    def write_ranking(
        self,
        entity_id: str,
        category_id: str,
        score: float,
        rank: int,
        explanation_json: str,
        now: str,
    ) -> None:
        ranking_id = _id_for("ranking", entity_id, category_id, SCORE_PROFILE_VERSION)
        self._conn.execute(
            """
            INSERT INTO ranking_results (
                ranking_id, entity_id, category_id, score, rank, profile_version,
                explanation_json, calculated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ranking_id) DO UPDATE SET
                score=excluded.score, rank=excluded.rank,
                explanation_json=excluded.explanation_json, calculated_at=excluded.calculated_at
            """,
            (ranking_id, entity_id, category_id, score, rank, SCORE_PROFILE_VERSION, explanation_json, now),
        )
        self._conn.commit()

    def rankings_for_category(self, category_id: str) -> list[sqlite3.Row]:
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute(
            """
            SELECT r.*, e.canonical_name, e.tagline FROM ranking_results r
            JOIN entities e ON e.entity_id = r.entity_id
            WHERE r.category_id = ? AND r.profile_version = ?
            ORDER BY r.rank ASC
            """,
            (category_id, SCORE_PROFILE_VERSION),
        )
        return cur.fetchall()

    # -- monthly archive ---------------------------------------------------

    def write_archive_snapshot_row(
        self,
        month_key: str,
        category_id: str,
        category_name: str,
        category_definition: str,
        entity_id: str,
        canonical_name: str,
        tagline: str | None,
        score: float,
        rank: int,
        positive_factors_json: str,
        negative_factors_json: str,
        snapshotted_at: str,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO archive_snapshots (
                month_key, category_id, category_name, category_definition,
                entity_id, canonical_name, tagline, score, rank,
                positive_factors_json, negative_factors_json, snapshotted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(month_key, category_id, entity_id) DO UPDATE SET
                category_name=excluded.category_name,
                category_definition=excluded.category_definition,
                canonical_name=excluded.canonical_name,
                tagline=excluded.tagline,
                score=excluded.score,
                rank=excluded.rank,
                positive_factors_json=excluded.positive_factors_json,
                negative_factors_json=excluded.negative_factors_json,
                snapshotted_at=excluded.snapshotted_at
            """,
            (
                month_key, category_id, category_name, category_definition,
                entity_id, canonical_name, tagline, score, rank,
                positive_factors_json, negative_factors_json, snapshotted_at,
            ),
        )
        self._conn.commit()

    def archive_months(self) -> list[str]:
        cur = self._conn.execute(
            "SELECT DISTINCT month_key FROM archive_snapshots ORDER BY month_key DESC"
        )
        return [row[0] for row in cur.fetchall()]

    def archive_snapshot_for_month(self, month_key: str) -> list[sqlite3.Row]:
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute(
            """
            SELECT * FROM archive_snapshots WHERE month_key = ?
            ORDER BY category_name ASC, rank ASC
            """,
            (month_key,),
        )
        return cur.fetchall()
