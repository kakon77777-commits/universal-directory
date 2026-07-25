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
        "filter_placeholder": "Filter by name or tagline…",
        "no_results": "No tools match your filter.",
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
        "nav_archive": "Archive",
        "archive_index_title": "Monthly Archive",
        "archive_index_intro": (
            "A frozen, month-by-month snapshot of every category's rankings — since this "
            "directory is mostly AI tools and models, it doubles as a running record of how "
            "that field itself evolves. Landing on the site always shows the current "
            "ranking; this is the history behind it."
        ),
        "archive_no_months": "No archived snapshots yet — check back after this month ends.",
        "archive_banner": "You're viewing an archived snapshot from {month}, not the current ranking.",
        "archive_view_latest": "View the current ranking →",
        "archive_month_of": "Archived snapshot: {month}",
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
        "filter_placeholder": "依名稱或簡介篩選…",
        "no_results": "沒有符合篩選條件的工具。",
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
        "nav_archive": "歷史存檔",
        "archive_index_title": "月度歷史存檔",
        "archive_index_intro": (
            "每個分類排名的月度凍結快照——因為這個目錄收錄的大多是 AI 工具與模型，它同時也成了"
            "這個領域自身演化的紀錄。進站看到的永遠是目前排名；這裡是排名背後的歷史。"
        ),
        "archive_no_months": "目前還沒有歷史存檔——這個月結束後再回來看看。",
        "archive_banner": "你正在檢視 {month} 的歷史存檔快照，不是目前的排名。",
        "archive_view_latest": "查看目前排名 →",
        "archive_month_of": "歷史存檔：{month}",
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
    # categories, 2026-07-25 expansion
    "General-Purpose Language Models": "通用大型語言模型",
    "Open-weight large language models released by major AI labs, usable outside any "
    "single vendor's hosted API.": "由主要 AI 實驗室釋出的開放權重大型語言模型，可脫離任何單一廠商的託管 API 使用。",
    "AI Coding Agents": "AI 程式開發 Agent",
    "Agents and assistants that read, write, and execute code autonomously or "
    "semi-autonomously inside a developer's own environment.": "在開發者自己的環境中自主或半自主地閱讀、撰寫與執行程式碼的 Agent 與助理。",
    "Local Model Tools": "本地模型工具",
    "Runtimes, servers, and interfaces for running language models on your own "
    "hardware instead of a hosted API.": "在自有硬體上執行語言模型的執行環境、伺服器與介面，取代託管 API。",
    "Vector Databases": "向量資料庫",
    "Databases and search engines purpose-built for storing and querying "
    "high-dimensional embedding vectors.": "專為儲存與查詢高維嵌入向量而設計的資料庫與搜尋引擎。",
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
    # entity taglines, 2026-07-25 expansion
    "Meta's family of open-weight large language models": "Meta 的開放權重大型語言模型家族",
    "Alibaba's open-weight large language model family": "阿里巴巴的開放權重大型語言模型家族",
    "DeepSeek's open-weight mixture-of-experts language model": "DeepSeek 的開放權重混合專家（MoE）語言模型",
    "Google DeepMind's family of lightweight open-weight models": "Google DeepMind 的輕量開放權重模型家族",
    "Open-source AI code assistant for any IDE": "適用於任何 IDE 的開源 AI 程式碼助理",
    "AI pair programming in your terminal": "在終端機中進行 AI 結對程式設計",
    "Open-source, extensible AI agent that installs, executes, edits, and tests code": "可安裝、執行、編輯與測試程式碼的開源可擴充 AI Agent",
    "Open-source terminal coding agent": "開源終端機程式開發 Agent",
    "AI agent platform for autonomous software development": "用於自主軟體開發的 AI Agent 平台",
    "Run large language models locally": "在本地執行大型語言模型",
    "LLM inference in C/C++, runs on commodity hardware": "以 C/C++ 實作的 LLM 推論引擎，可在一般硬體上運行",
    "High-throughput, memory-efficient inference and serving engine for LLMs": "高吞吐量、高記憶體效率的 LLM 推論與服務引擎",
    "High-performance serving framework for language and multimodal models": "高效能的語言與多模態模型服務框架",
    "Open-source desktop app and web UI for running local LLMs": "用於執行本地 LLM 的開源桌面應用程式與網頁介面",
    "Vector similarity search engine and database": "向量相似度搜尋引擎與資料庫",
    "Open-source vector database built for scalable similarity search": "為可擴展相似度搜尋而打造的開源向量資料庫",
    "Open-source vector database with built-in ML model integrations": "內建機器學習模型整合的開源向量資料庫",
    "Open-source embedding database for AI applications": "為 AI 應用打造的開源嵌入資料庫",
    "Open-source vector similarity search extension for PostgreSQL": "PostgreSQL 的開源向量相似度搜尋擴充套件",
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
