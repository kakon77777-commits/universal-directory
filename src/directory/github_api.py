"""Thin GitHub REST API client — Tier 1 evidence (doc section 35: 官方文件/正式API)."""

from __future__ import annotations

import logging
import os

import httpx

GITHUB_API_BASE = "https://api.github.com"
logger = logging.getLogger("directory.github_api")


async def fetch_repo(client: httpx.AsyncClient, owner_repo: str) -> dict | None:
    url = f"{GITHUB_API_BASE}/repos/{owner_repo}"
    headers = {"Accept": "application/vnd.github+json"}
    # Unauthenticated GitHub API calls are capped at 60/hour — fine for a
    # handful of entities, but the catalog is expected to keep growing
    # (doc2's own MVP stage-1 range is 100-300 entities) and every
    # `directory build` re-ingests the whole catalog every time. An
    # optional token (e.g. `gh auth token`) raises that to 5000/hour;
    # falls back to unauthenticated if unset, same as before.
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = await client.get(url, headers=headers, timeout=20.0)
    if resp.status_code != 200:
        logger.warning("GitHub API returned %s for %s", resp.status_code, owner_repo)
        return None
    return resp.json()
