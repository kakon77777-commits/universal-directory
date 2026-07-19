"""CLI: `directory ingest` (populate DB) or `directory build` (ingest + generate static site)."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import logging
import sys
from pathlib import Path

from .ingest import ingest
from .sitegen import build_site
from .store import DirectoryStore

DEFAULT_CONFIG_DIR = Path("config")
DEFAULT_DB_PATH = Path("storage/metadata/directory.db")
DEFAULT_SITE_DIR = Path("site")
DEFAULT_SOURCE_DOC = r"D:\我的研究\未來計畫區\網路爬蟲_AI爬蟲與Agent自動化搜尋技術整理_2026-07-14.md"
USER_AGENT = "EVEMISS-DirectoryBot/0.1 (+https://evemisslab.com)"


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
            build_site(store, args.site_dir, _now())
            print(f"site generated at {args.site_dir}")
    finally:
        store.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
