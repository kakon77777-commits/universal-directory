# universal-directory

MVP of the "通用動態策展目錄" (Universal Dynamic Curated Directory, UDCD)
described in
`通用動態策展目錄_Agent自動治理平台_技術白皮書與概念論文_2026-07-14.md`.
This is also the real-world test bed for
[ai-web-research](https://github.com/kakon77777-commits/ai-web-research):
every piece of live data on this site was fetched by that crawler, not typed
in by hand.

**Deployment**: Cloudflare Pages project `universal-directory`
(`site/` deployed via `wrangler pages deploy site --project-name
universal-directory --branch main`), intended to live at
`directory.evemiss.com` (a subdomain of the EveMiss Technology hub,
`https://evemiss.com`). The Pages custom-domain registration is done via
the Cloudflare API; the DNS CNAME (`directory` →
`universal-directory.pages.dev`, proxied) has to be added by hand in the
Cloudflare dashboard for the `evemiss.com` zone — the wrangler OAuth
token used for deploys only has `zone:read`, not DNS-record write, so an
agent can't create it via API.

## Languages

English is the default/primary language; Traditional Chinese is the
secondary language — same architecture as evemiss.com (proxied through
this same session): a Cloudflare Pages Advanced Mode worker
(`site_worker/_worker.js`, copied to `site/_worker.js` on every build)
negotiates `lang` cookie > IP country > `Accept-Language` > English, and
[matrix-select](https://github.com/kakon77777-commits/matrix-select) is
the language switcher (copied into `site/` from its own source repo on
every build, same component embedded in evemiss.com and agiright.org).

`config/categories.yaml`/`config/entities.yaml` content
(name/definition/tagline) is English-source; `src/directory/i18n.py`'s
`CONTENT_ZH` holds the Traditional Chinese translations, keyed by the
exact English string — a string with no entry there just falls back to
English rather than erroring, so adding a third language later is
additive only (one more nested dict + one more `SUPPORTED_LANGS` entry),
no data-model change. `python -m directory build` generates every
supported language automatically: English at the site root, Chinese
under `/zh/`.

## Scope (doc2's own 階段一 MVP)

- 5 hand-defined categories, 16 hand-confirmed entities (`config/*.yaml`) —
  this stands in for Discovery Agent + 人工確認候選 for now.
- Ingestion pulls two evidence tiers per entity:
  - **Tier 1** (official API): GitHub REST API — stars, license (SPDX),
    last-push date, open issues, topics, archived flag.
  - **Tier 2** (generic web page): the entity's GitHub page, fetched through
    `ai-web-research`'s own `Fetcher` + deterministic meta/OG extractor.
- Every field is stored as evidence (`value`, `source_url`, `source_tier`,
  `fetched_at`, `confidence`) — not just a final cached value — per the
  claim/evidence model in doc2 section 34.
- Ranking is a **versioned, deterministic** formula (`open_source_ai_tools_v1`,
  see `src/directory/scoring.py`): 40% activity decay since last push + 40%
  log-normalized stars (within category) + 20% license permissiveness, minus a
  flat penalty if archived. No LLM makes ranking decisions — doc section 23's
  own principle ("真正分數由版本化程式計算") holds even without any AI agents
  wired up yet.
- Output is a static site (`site/`): homepage with per-category top-8, full
  ranked category pages, and entity pages showing the complete evidence
  table with sources.

Not in scope yet: LLM-driven Discovery/Identity/Classification/Verification/
Review agents (doc2's 階段四) — those need an LLM backend, deferred pending
API/credential setup. Everything here is deliberately agent-free and
reproducible from the raw evidence.

## Setup

```bash
uv venv
uv pip install -e ".[dev]"
```

This installs `ai-web-research` as a local path dependency
(`file:///D:/Ai/work%20together/ai-web-research` in `pyproject.toml`) — it
assumes both repos are checked out as siblings on the same machine. That's a
known limitation for an MVP tying two young projects together; revisit if
this needs to run somewhere else.

Playwright's Chromium browser is shared with `ai-web-research`'s install
(`playwright install chromium`), no need to re-download.

## Usage

```bash
# Ingest entities (GitHub API + crawled pages) into storage/metadata/directory.db
python -m directory ingest --verbose

# Ingest + regenerate the static site into site/
python -m directory build --verbose
```

Open `site/index.html` directly, or serve the folder with any static file
server.

## Tests

```bash
.venv/Scripts/python.exe -m pytest -q
```

28 unit tests cover the store, scoring formula edge cases (archived, missing
push date, unknown/mixed license), site generation, and the multi-language
build orchestration — no live network calls. The ingestion pipeline itself
is exercised live via `directory build` against the real GitHub API and
real GitHub pages.
