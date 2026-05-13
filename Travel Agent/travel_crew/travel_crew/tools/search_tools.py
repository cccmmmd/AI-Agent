"""
tools/search_tools.py
---------------------
自定義搜尋工具：使用 Brave Search API 查詢旅遊即時資訊。
每個 Agent 都會透過這個工具對外查詢。
"""

import os
import requests
from crewai.tools import tool


BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


def _brave_search(query: str, count: int = 2) -> str:
    """
    呼叫 Brave Search REST API，回傳純文字摘要。
    若 API Key 未設定，會拋出明確錯誤提示。
    """
    if not BRAVE_API_KEY:
        raise EnvironmentError(
            "找不到 BRAVE_API_KEY。請在 .env 或環境變數中設定。"
        )

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY,
    }
    params = {
        "q": query,
        "count": count,
        "text_decorations": "false",
        "search_lang": "zh-hant",   # 優先繁體中文結果
        "extra_snippets": "true",
    }

    response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    results = data.get("web", {}).get("results", [])
    if not results:
        return "未找到相關搜尋結果。"

    # 將結果整理成可讀文字，供 Agent 解析
    output_lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "無標題")
        url = r.get("url", "")
        desc = r.get("description", "")
        extra = " ".join(r.get("extra_snippets", []))
        output_lines.append(
            f"[結果 {i}] {title}\n來源：{url}\n摘要：{desc}\n補充：{extra}\n"
        )

    return "\n".join(output_lines)


# ──────────────────────────────────────────
# 以下每個 @tool 裝飾器都是獨立工具實例
# 分別給不同 Agent 使用，查詢關鍵字也不同
# ──────────────────────────────────────────

@tool("logistics_search")
def logistics_search(query: str) -> str:
    """
    搜尋旅遊目的地的天氣預報、氣候特徵、電壓插座規格、飲水安全與行動網路覆蓋率。
    輸入範例：\"Rome October weather forecast\" 或 \"Italy plug type voltage\"
    """
    return _brave_search(query)


@tool("financial_search")
def financial_search(query: str) -> str:
    """
    搜尋即時匯率、當地刷卡普及度、ATM 手續費、退稅門檻與流程。
    輸入範例：\"EUR TWD exchange rate 2026\" 或 \"Italy VAT refund tourist\"
    """
    return _brave_search(query)


@tool("safety_culture_search")
def safety_culture_search(query: str) -> str:
    """
    搜尋旅遊目的地的文化禁忌、宗教禮儀、常見旅遊詐騙手法與緊急聯絡電話。
    輸入範例：\"Italy tourist scam 2026\" 或 \"Rome cultural etiquette tips\"
    """
    return _brave_search(query)
