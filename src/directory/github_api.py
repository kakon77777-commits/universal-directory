"""Thin GitHub REST API client — Tier 1 evidence (doc section 35: 官方文件/正式API)."""

from __future__ import annotations

import logging

import httpx

GITHUB_API_BASE = "https://api.github.com"
logger = logging.getLogger("directory.github_api")


async def fetch_repo(client: httpx.AsyncClient, owner_repo: str) -> dict | None:
    url = f"{GITHUB_API_BASE}/repos/{owner_repo}"
    resp = await client.get(url, headers={"Accept": "application/vnd.github+json"}, timeout=20.0)
    if resp.status_code != 200:
        logger.warning("GitHub API returned %s for %s", resp.status_code, owner_repo)
        return None
    return resp.json()
