"""Static site generator: entities/categories/evidence -> HTML.

Doc section 7-10 information architecture: homepage (category overview +
top entities), category pages (full ranked list + methodology), entity
detail pages (tagline, evidence-backed fields with sources, last-verified
time).
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .scoring import PROFILE_VERSION, score_category
from .store import DirectoryStore

TEMPLATES_DIR = Path(__file__).parent / "templates"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "entity"


def _display_value(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "—"
    if isinstance(value, bool):
        return "是" if value else "否"
    return str(value)


def _evidence_view(store: DirectoryStore, entity_id: str) -> list[dict]:
    return [
        {
            "field_name": r["field_name"],
            "value": _display_value(json.loads(r["value_json"])),
            "source_url": r["source_url"],
            "source_tier": r["source_tier"],
            "fetched_at": r["fetched_at"],
            "confidence": r["confidence"],
        }
        for r in store.evidence_for_entity(entity_id)
    ]


def _entity_view(store: DirectoryStore, entity_row) -> dict:
    entity_id = entity_row["entity_id"]
    return {
        "entity_id": entity_id,
        "slug": slugify(entity_row["canonical_name"]),
        "canonical_name": entity_row["canonical_name"],
        "tagline": entity_row["tagline"],
        "description": entity_row["description"],
        "urls": store.entity_urls(entity_id),
        "updated_at": entity_row["updated_at"],
    }


def _ranked_entity_views(store: DirectoryStore, category_id: str) -> list[dict]:
    ranked = score_category(store, category_id)
    entity_rows = {r["entity_id"]: r for r in store.entities_in_category(category_id)}

    views = []
    for rank, scored in enumerate(ranked, start=1):
        view = _entity_view(store, entity_rows[scored.entity_id])
        view["rank"] = rank
        view["score"] = scored.score
        view["positive_factors"] = scored.positive_factors
        view["negative_factors"] = scored.negative_factors
        views.append(view)
    return views


def build_site(store: DirectoryStore, output_dir: Path, now_iso: str) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )

    categories = store.all_categories()
    category_rankings = {cat["category_id"]: _ranked_entity_views(store, cat["category_id"]) for cat in categories}

    index_template = env.get_template("index.html.jinja")
    category_summaries = [
        {
            "category_id": cat["category_id"],
            "name": cat["name"],
            "definition": cat["definition"],
            "count": len(category_rankings[cat["category_id"]]),
            "top_entities": category_rankings[cat["category_id"]][:8],
        }
        for cat in categories
    ]
    (output_dir / "index.html").write_text(
        index_template.render(
            categories=category_summaries, generated_at=now_iso, profile_version=PROFILE_VERSION
        ),
        encoding="utf-8",
    )

    category_template = env.get_template("category.html.jinja")
    for cat in categories:
        cat_dir = output_dir / "categories" / cat["category_id"]
        cat_dir.mkdir(parents=True, exist_ok=True)
        (cat_dir / "index.html").write_text(
            category_template.render(
                category=cat,
                entities=category_rankings[cat["category_id"]],
                generated_at=now_iso,
                profile_version=PROFILE_VERSION,
            ),
            encoding="utf-8",
        )

    entity_template = env.get_template("entity.html.jinja")
    for entity_row in store.all_entities():
        view = _entity_view(store, entity_row)
        view["evidence"] = _evidence_view(store, entity_row["entity_id"])
        view["categories"] = [
            {"category_id": c["category_id"], "name": c["name"]}
            for c in store.categories_for_entity(entity_row["entity_id"])
        ]
        entity_dir = output_dir / "entities" / view["slug"]
        entity_dir.mkdir(parents=True, exist_ok=True)
        (entity_dir / "index.html").write_text(
            entity_template.render(entity=view, generated_at=now_iso),
            encoding="utf-8",
        )
