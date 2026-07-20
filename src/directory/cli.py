"""CLI: `directory ingest` (populate DB) or `directory build` (ingest + generate static site)."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import logging
import shutil
import sys
from pathlib import Path

from .i18n import DEFAULT_LANG, SUPPORTED_LANGS
from .ingest import ingest
from .sitegen import build_site
from .store import DirectoryStore

DEFAULT_CONFIG_DIR = Path("config")
DEFAULT_DB_PATH = Path("storage/metadata/directory.db")
DEFAULT_SITE_DIR = Path("site")
DEFAULT_SOURCE_DOC = r"D:\我的研究\未來計畫區\網路爬蟲_AI爬蟲與Agent自動化搜尋技術整理_2026-07-14.md"
USER_AGENT = "EVEMISS-DirectoryBot/0.1 (+https://evemisslab.com)"

# Static assets copied to the site root on every build — matrix-select (the
# language switcher, same component/approach as evemiss.com and
# agiright.org) and the Cloudflare Pages Advanced Mode worker that does
# language negotiation (cookie > country > Accept-Language > English).
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MATRIX_SELECT_SRC = Path(r"D:\Ai\work together\matrix-select\src")
WORKER_SRC = REPO_ROOT / "site_worker" / "_worker.js"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="directory")
    parser.add_argument("command", choices=["ingest", "build"])
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--site-dir", type=Path, default=DEFAULT_SITE_DIR)
    parser.add_argument("--verbose", action="store_true")
    return parser


def _build_all_languages(store: DirectoryStore, site_dir: Path, now_iso: str) -> None:
    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir(parents=True, exist_ok=True)

    for lang in SUPPORTED_LANGS:
        target = site_dir if lang == DEFAULT_LANG else site_dir / lang
        build_site(store, target, now_iso, lang=lang)

    for asset in ("matrix-select.js", "matrix-select.css"):
        shutil.copy(MATRIX_SELECT_SRC / asset, site_dir / asset)
    shutil.copy(WORKER_SRC, site_dir / "_worker.js")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    store = DirectoryStore(args.db)
    try:
        asyncio.run(ingest(args.config_dir, store, USER_AGENT, DEFAULT_SOURCE_DOC))
        if args.command == "build":
            _build_all_languages(store, args.site_dir, _now())
            print(f"site generated at {args.site_dir} ({', '.join(SUPPORTED_LANGS)})")
    finally:
        store.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
