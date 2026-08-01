"""Static site generator: entities/categories/evidence -> HTML.

Doc section 7-10 information architecture: homepage (category overview +
top entities), category pages (full ranked list + methodology), entity
detail pages (tagline, evidence-backed fields with sources, last-verified
time).

i18n: English is the default/primary language (config/*.yaml content is
English-source); build_site() is called once per language by the caller,
each into its own output_dir (see cli.py) — this function itself no longer
owns cleaning the output tree, since a caller building multiple languages
into sibling directories under one site root must only clean that root
once, not per-language-call (see src/directory/i18n.py for the
translation layer, and cli.py for the multi-language build orchestration).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .i18n import DEFAULT_LANG, Lang, LANG_META, content as t_content, ui
from .scoring import PROFILE_VERSION, score_category
from .store import DirectoryStore

TEMPLATES_DIR = Path(__file__).parent / "templates"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "entity"


_EN_MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

ARCHIVE_GRANULARITIES = ("week", "month", "year")


def _period_label(granularity: str, period_key: str, lang: Lang) -> str:
    """period_key shapes are fixed by cli.py's `_period_keys()`: week
    "YYYY-Www" (ISO week), month "YYYY-MM", year "YYYY" — plain slices/
    formats, never arbitrary date strings, so each branch only needs to
    handle its one known shape."""
    if granularity == "week":
        year, week = period_key.split("-W")
        if lang == "zh":
            return f"{year}年第{int(week)}週"
        return f"Week {int(week)}, {year}"
    if granularity == "month":
        year, month = period_key.split("-")
        if lang == "zh":
            return f"{year}年{int(month)}月"
        return f"{_EN_MONTH_NAMES[int(month) - 1]} {year}"
    return period_key  # year: the bare "YYYY" is already the label in both languages


def _display_value(value: object, t: dict[str, str]) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "—"
    if isinstance(value, bool):
        return t["yes"] if value else t["no"]
    return str(value)


def _evidence_view(store: DirectoryStore, entity_id: str, t: dict[str, str]) -> list[dict]:
    return [
        {
            "field_name": r["field_name"],
            "value": _display_value(json.loads(r["value_json"]), t),
            "source_url": r["source_url"],
            "source_tier": r["source_tier"],
            "fetched_at": r["fetched_at"],
            "confidence": r["confidence"],
        }
        for r in store.evidence_for_entity(entity_id)
    ]


def _entity_view(store: DirectoryStore, entity_row, lang: Lang) -> dict:
    entity_id = entity_row["entity_id"]
    return {
        "entity_id": entity_id,
        "slug": slugify(entity_row["canonical_name"]),
        "canonical_name": entity_row["canonical_name"],
        "tagline": t_content(entity_row["tagline"], lang) if entity_row["tagline"] else entity_row["tagline"],
        "description": entity_row["description"],  # already English (GitHub API), no translation needed
        "urls": store.entity_urls(entity_id),
        "updated_at": entity_row["updated_at"],
    }


def _ranked_entity_views(store: DirectoryStore, category_id: str, lang: Lang) -> list[dict]:
    ranked = score_category(store, category_id)
    entity_rows = {r["entity_id"]: r for r in store.entities_in_category(category_id)}

    views = []
    for rank, scored in enumerate(ranked, start=1):
        view = _entity_view(store, entity_rows[scored.entity_id], lang)
        view["rank"] = rank
        view["score"] = scored.score
        view["positive_factors"] = scored.positive_factors
        view["negative_factors"] = scored.negative_factors
        views.append(view)
    return views


def build_site(store: DirectoryStore, output_dir: Path, now_iso: str, lang: Lang = DEFAULT_LANG) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )

    t = ui(lang)
    html_lang = LANG_META.get(lang, LANG_META[DEFAULT_LANG])["html"]

    categories = store.all_categories()
    category_rankings = {
        cat["category_id"]: _ranked_entity_views(store, cat["category_id"], lang) for cat in categories
    }

    index_template = env.get_template("index.html.jinja")
    category_summaries = [
        {
            "category_id": cat["category_id"],
            "name": t_content(cat["name"], lang),
            "definition": t_content(cat["definition"], lang),
            "count": len(category_rankings[cat["category_id"]]),
            "top_entities": category_rankings[cat["category_id"]][:8],
        }
        for cat in categories
    ]
    (output_dir / "index.html").write_text(
        index_template.render(
            categories=category_summaries,
            generated_at=now_iso,
            profile_version=PROFILE_VERSION,
            t=t,
            html_lang=html_lang,
            lang=lang,
        ),
        encoding="utf-8",
    )

    category_template = env.get_template("category.html.jinja")
    for cat in categories:
        cat_view = {
            "category_id": cat["category_id"],
            "name": t_content(cat["name"], lang),
            "definition": t_content(cat["definition"], lang),
        }
        cat_dir = output_dir / "categories" / cat["category_id"]
        cat_dir.mkdir(parents=True, exist_ok=True)
        (cat_dir / "index.html").write_text(
            category_template.render(
                category=cat_view,
                entities=category_rankings[cat["category_id"]],
                generated_at=now_iso,
                profile_version=PROFILE_VERSION,
                t=t,
                html_lang=html_lang,
                lang=lang,
            ),
            encoding="utf-8",
        )

    entity_template = env.get_template("entity.html.jinja")
    for entity_row in store.all_entities():
        view = _entity_view(store, entity_row, lang)
        view["evidence"] = _evidence_view(store, entity_row["entity_id"], t)
        view["categories"] = [
            {"category_id": c["category_id"], "name": t_content(c["name"], lang)}
            for c in store.categories_for_entity(entity_row["entity_id"])
        ]
        entity_dir = output_dir / "entities" / view["slug"]
        entity_dir.mkdir(parents=True, exist_ok=True)
        (entity_dir / "index.html").write_text(
            entity_template.render(entity=view, generated_at=now_iso, t=t, html_lang=html_lang, lang=lang),
            encoding="utf-8",
        )

    _build_archive(store, output_dir, env, t, html_lang, lang)


def _build_archive(
    store: DirectoryStore, output_dir: Path, env: Environment, t: dict[str, str], html_lang: str, lang: Lang
) -> None:
    """Renders the archive tree (/archive/, /archive/{granularity}/{period}/)
    from `archive_snapshots` — a separate, denormalized table (see
    store.py), not a live query, so every past period's page renders
    exactly what was true when it was snapshotted even after categories/
    entities change later. Re-rendered in full on every build (cheap —
    it's templating over already-computed rows, no network calls), which
    is deliberate: template/styling changes should apply retroactively to
    old archive pages too, not freeze the HTML itself — only the DATA is
    frozen. Three granularities (week/month/year), week listed first —
    Neo: "先以周為單位。然後才是月，年"."""
    archive_dir = output_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    periods_by_granularity = {g: store.archive_periods(g) for g in ARCHIVE_GRANULARITIES}

    archive_index_template = env.get_template("archive_index.html.jinja")
    sections = [
        {
            "granularity": g,
            "heading": t[f"archive_by_{g}"],
            "periods": [{"period_key": p, "label": _period_label(g, p, lang)} for p in periods_by_granularity[g]],
        }
        for g in ARCHIVE_GRANULARITIES
    ]
    (archive_dir / "index.html").write_text(
        archive_index_template.render(sections=sections, t=t, html_lang=html_lang, lang=lang),
        encoding="utf-8",
    )

    archive_period_template = env.get_template("archive_period.html.jinja")
    for granularity in ARCHIVE_GRANULARITIES:
        for period_key in periods_by_granularity[granularity]:
            rows = store.archive_snapshot_for_period(granularity, period_key)
            categories_by_id: dict[str, dict] = {}
            for r in rows:
                cat = categories_by_id.setdefault(
                    r["category_id"],
                    {
                        "category_id": r["category_id"],
                        "name": t_content(r["category_name"], lang),
                        "definition": t_content(r["category_definition"], lang),
                        "entities": [],
                    },
                )
                cat["entities"].append(
                    {
                        "slug": slugify(r["canonical_name"]),
                        "canonical_name": r["canonical_name"],
                        "tagline": t_content(r["tagline"], lang) if r["tagline"] else r["tagline"],
                        "score": r["score"],
                        "rank": r["rank"],
                        "positive_factors": json.loads(r["positive_factors_json"]),
                        "negative_factors": json.loads(r["negative_factors_json"]),
                    }
                )

            period_dir = archive_dir / granularity / period_key
            period_dir.mkdir(parents=True, exist_ok=True)
            (period_dir / "index.html").write_text(
                archive_period_template.render(
                    period_key=period_key,
                    period_label=_period_label(granularity, period_key, lang),
                    categories=sorted(categories_by_id.values(), key=lambda c: c["name"]),
                    t=t,
                    html_lang=html_lang,
                    lang=lang,
                ),
                encoding="utf-8",
            )
