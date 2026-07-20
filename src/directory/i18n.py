"""Minimal two-language (en default, zh secondary) i18n layer.

English is now the canonical/primary language — config/entities.yaml and
config/categories.yaml's tagline/name/definition fields are written in
English. CONTENT_ZH and UI_STRINGS below translate that same English text
(plus the templates' static chrome) to Traditional Chinese, keyed by the
exact English source string — the same pattern already proven working
across evemiss.com and agiright.org: a string with no entry here just
falls back to English instead of erroring, so this scales to future
languages the same way a translator agent would extend it (one more
nested dict, nothing else changes).
"""

from __future__ import annotations

Lang = str  # "en" | "zh" — kept a plain str, matching this codebase's style elsewhere

DEFAULT_LANG: Lang = "en"
SUPPORTED_LANGS: tuple[Lang, ...] = ("en", "zh")

LANG_META: dict[Lang, dict[str, str]] = {
    "en": {"html": "en", "label": "English"},
    "zh": {"html": "zh-Hant", "label": "繁體中文"},
}

UI_STRINGS: dict[Lang, dict[str, str]] = {
    "en": {
        "site_title": "Universal Dynamic Curated Directory",
        "site_title_short": "UDCD MVP",
        "footer_credit": (
            'Crawled by <a href="https://github.com/kakon77777-commits/ai-web-research">'
            "ai-web-research</a>, ranked by deterministic versioned scoring code "
            "(no LLM judges the ranking)."
        ),
        "index_title": "Universal Dynamic Curated Directory — AI Crawler & Agent Tools",
        "generated_at_label": "Last generated: ",
        "index_intro": (
            "Scope: open-source tools for AI crawlers, browser agents, deep research "
            "agents, and agent orchestration platforms. Every score is computed by "
            "versioned code ({profile_version}) from GitHub activity, stars, and "
            "license — never by subjective model judgment."
        ),
        "items_suffix": "items",
        "view_full_ranking": "View full ranking →",
        "back_home": "← Back to home",
        "methodology": (
            "Scoring method ({profile_version}): 40% GitHub activity (time-decay "
            "since last push) + 40% stars (log-normalized within category) + 20% "
            "license permissiveness, minus 5 points if archived. Last generated: "
            "{generated_at}"
        ),
        "th_rank": "#",
        "th_name": "Name",
        "th_score": "Score",
        "th_notes": "Notes",
        "th_field": "Field",
        "th_value": "Value",
        "th_source": "Source",
        "th_tier": "Tier",
        "th_fetched": "Fetched",
        "th_confidence": "Confidence",
        "official_website": "Official website",
        "last_updated_label": "Last updated: ",
        "evidence_chain_heading": "Evidence Chain",
        "yes": "Yes",
        "no": "No",
    },
    "zh": {
        "site_title": "通用動態策展目錄",
        "site_title_short": "UDCD MVP",
        "footer_credit": (
            '由 <a href="https://github.com/kakon77777-commits/ai-web-research">'
            "ai-web-research</a> 爬取、以確定性版本化程式評分（無 LLM 判斷排名）。"
        ),
        "index_title": "通用動態策展目錄 — AI 爬蟲與 Agent 工具",
        "generated_at_label": "最後產生：",
        "index_intro": (
            "收錄範圍：AI 爬蟲、瀏覽器 Agent、深度研究 Agent 與 Agent 編排平台的開源"
            "工具。每個項目的分數皆由版本化程式（{profile_version}）依 GitHub 活躍"
            "度、星數與授權計算，不由模型主觀判斷。"
        ),
        "items_suffix": "項",
        "view_full_ranking": "查看完整排行 →",
        "back_home": "← 返回首頁",
        "methodology": (
            "評分方式（{profile_version}）：40% GitHub 活躍度（距上次 push 的時間衰"
            "減）+ 40% 星數（同分類內以 log 正規化）+ 20% 授權寬鬆度，Archived 專案扣 "
            "5 分。最後產生：{generated_at}"
        ),
        "th_rank": "#",
        "th_name": "名稱",
        "th_score": "分數",
        "th_notes": "說明",
        "th_field": "欄位",
        "th_value": "值",
        "th_source": "來源",
        "th_tier": "Tier",
        "th_fetched": "抓取時間",
        "th_confidence": "信心",
        "official_website": "官方網站",
        "last_updated_label": "最後更新：",
        "evidence_chain_heading": "證據鏈（Evidence）",
        "yes": "是",
        "no": "否",
    },
}

# Content translations (category name/definition, entity tagline) — keyed
# by the exact English source string from config/*.yaml. A key with no
# entry here just isn't in CONTENT_ZH; callers fall back to the English
# source, same fallback behavior as UI_STRINGS.
CONTENT_ZH: dict[str, str] = {
    # categories
    "AI Crawlers": "AI 爬蟲",
    "Crawler Frameworks": "爬蟲框架",
    "Browser Agents": "瀏覽器 Agent",
    "Deep Research Agents": "深度研究 Agent",
    "Agent Orchestration Platforms": "Agent 編排平台",
    "Crawling tools that use semantic models to understand pages, generate or repair "
    "extraction rules, or convert web pages into LLM-usable formats.": "使用語義模型理解頁面、生成/修復抽取規則、或將網頁轉為 LLM 可用格式的爬蟲工具。",
    "Frameworks providing deterministic crawling infrastructure — URL frontier, retry, "
    "rate limiting, session management.": "提供 URL Frontier、重試、限速、Session 管理等確定性爬蟲工程底座的框架。",
    "AI-driven automation tools that autonomously decide browser interactions — "
    "clicking, typing, scrolling, navigating.": "由 AI 驅動、可自行決定點擊/輸入/滾動/導航等瀏覽器互動的自動化工具。",
    "Research agents that automatically search, read, cross-verify multiple sources, "
    "and generate cited reports.": "自動搜尋、閱讀、交叉查證多來源並生成附引用報告的研究型 Agent。",
    "Platforms providing scheduling, skills, multi-agent routing, and long-running "
    "control planes.": "提供排程、技能、多 Agent 路由與長時間運行控制平面的平台。",
    # entity taglines
    "Local, self-hosted, LLM-friendly web crawler": "本地、自架、LLM-Friendly Web Crawler",
    "Full Web Context API and agent web-data platform": "完整 Web Context API 與 Agent Web Data 平台",
    "Natural-language-driven graph-based data extraction framework": "自然語言驅動的圖式資料抽取框架",
    "Modern Python crawling and browser automation engineering foundation": "現代 Python 爬蟲與瀏覽器自動化工程底座",
    "Rust-built CLI, MCP, and self-hosted web extraction tool": "Rust 實作的 CLI、MCP 與自架網頁抽取工具",
    "General-purpose AI browser agent": "通用 AI Browser Agent",
    "Production-grade browser automation framework mixing AI and code": "AI 與程式碼混合的生產級瀏覽器自動化框架",
    "Workflow automation platform combining LLMs, vision models, and Playwright": "LLM、視覺模型與 Playwright 結合的工作流自動化平台",
    "Local multi-agent browser extension running directly in Chrome/Edge": "直接運行於 Chrome／Edge 的本地多 Agent 擴充功能",
    "Full open-source deep research agent": "完整的開源深度研究 Agent",
    "Configurable deep research agent in the LangGraph ecosystem": "LangGraph 生態的可配置深度研究 Agent",
    "Competitive intelligence, continuous monitoring, and research knowledge-base "
    "platform": "競爭情報、持續監測與研究知識庫平台",
    "Private documents, vector database, and deep search": "私有文件、向量資料庫與深度搜尋",
    "Local-first, long-running personal agent control plane": "本地優先、長時間運行的個人 Agent 控制平面",
    "Enterprise-grade agent command center": "公司級 Agent Command Center",
    "Deterministic, LLM-independent robots/sitemap-aware crawler producing LLM-ready "
    "Markdown with a resumable frontier": "確定性、無 LLM 依賴的 robots/sitemap-aware 爬蟲，輸出 LLM 可用 Markdown 與可續傳 frontier",
}


def ui(lang: Lang) -> dict[str, str]:
    return UI_STRINGS.get(lang, UI_STRINGS[DEFAULT_LANG])


def content(text: str, lang: Lang) -> str:
    """Translate a piece of English-source content (category name/definition,
    entity tagline) to `lang`, falling back to the English source if no
    translation exists for this exact string."""
    if lang == DEFAULT_LANG:
        return text
    return CONTENT_ZH.get(text, text)
