"""Ingestion: seed entities/categories from config, then populate evidence
from the GitHub REST API (Tier 1: official API) and a crawled GitHub page
(Tier 2: generic web source), fetched via the ai-web-research crawler — the
whole point of this project per the two source docs.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path

import httpx
import yaml
from crawler.extract import extract_metadata
from crawler.fetcher import Fetcher

from .github_api import fetch_repo
from .store import DirectoryStore, Evidence

logger = logging.getLogger("directory.ingest")

TIER_OFFICIAL_API = 1
TIER_GITHUB_PAGE = 2
TIER_INTERNAL_DOC = 3


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_categories(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["categories"]


def load_entities(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["entities"]


async def ingest(config_dir: Path, store: DirectoryStore, user_agent: str, source_doc_path: str) -> None:
    categories = load_categories(config_dir / "categories.yaml")
    entities = load_entities(config_dir / "entities.yaml")
    now = _now()

    for cat in categories:
        store.upsert_category(
            category_id=cat["category_id"],
            name=cat["name"],
            definition=cat["definition"],
            parent_id=cat.get("parent_id"),
            ranking_profile=cat["ranking_profile"],
        )

    async with httpx.AsyncClient(follow_redirects=True) as gh_client:
        async with Fetcher(user_agent=user_agent, timeout_seconds=20.0, retry_count=2) as fetcher:
            for spec in entities:
                github_url = f"https://github.com/{spec['github_repo']}"
                repo_data = await fetch_repo(gh_client, spec["github_repo"])
                description = repo_data.get("description") if repo_data else None

                entity_id = store.upsert_entity(
                    canonical_name=spec["canonical_name"],
                    entity_type=spec["entity_type"],
                    tagline=spec["tagline"],
                    description=description,
                    now=now,
                    aliases=[spec["github_repo"]],
                    urls={"github": github_url, "homepage": github_url},
                )
                store.link_entity_category(
                    entity_id, spec["primary_category"], relation_type="primary", confidence=1.0
                )

                store.add_evidence(Evidence(
                    entity_id=entity_id,
                    field_name="license_hint_from_doc",
                    value_json=json.dumps(spec["license_hint"]),
                    source_url=source_doc_path,
                    source_text=None,
                    source_tier=TIER_INTERNAL_DOC,
                    fetched_at=now,
                    confidence=0.8,
                ))

                if repo_data is not None:
                    api_fields = {
                        "description": repo_data.get("description"),
                        "stars": repo_data.get("stargazers_count"),
                        "license": (repo_data.get("license") or {}).get("spdx_id"),
                        "pushed_at": repo_data.get("pushed_at"),
                        "open_issues": repo_data.get("open_issues_count"),
                        "topics": repo_data.get("topics"),
                        "archived": repo_data.get("archived"),
                    }
                    for field_name, value in api_fields.items():
                        if value is None:
                            continue
                        store.add_evidence(Evidence(
                            entity_id=entity_id,
                            field_name=field_name,
                            value_json=json.dumps(value),
                            source_url=f"https://api.github.com/repos/{spec['github_repo']}",
                            source_text=None,
                            source_tier=TIER_OFFICIAL_API,
                            fetched_at=now,
                            confidence=0.99,
                        ))
                else:
                    logger.warning("no GitHub API data for %s", spec["canonical_name"])

                fetch_result = await fetcher.fetch(github_url)
                if fetch_result.success:
                    meta = extract_metadata(fetch_result.html, fetch_result.final_url)
                    if meta.title:
                        store.add_evidence(Evidence(
                            entity_id=entity_id,
                            field_name="page_title",
                            value_json=json.dumps(meta.title),
                            source_url=github_url,
                            source_text=meta.title,
                            source_tier=TIER_GITHUB_PAGE,
                            fetched_at=now,
                            confidence=0.9,
                        ))
                else:
                    logger.warning(
                        "homepage fetch failed for %s: %s",
                        spec["canonical_name"], fetch_result.error_message,
                    )

                logger.info("ingested %s", spec["canonical_name"])
