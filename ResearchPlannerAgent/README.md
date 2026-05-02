# Multi-Agent Research Assistant

> 由三個 Agent 協作，從「提出問題」到「產出報告」的全自動 AI 研究助手。

---

## 這個專案想要解決

**手動研究太耗時**：找資料、篩關鍵字、整理來源、撰寫摘要，這些步驟加起來往往要花數小時。

這個專案把整個流程自動化：你只需要用一句話描述研究主題，系統就會幫你規劃研究方向、搜尋網路、整理成一份附有來源連結的 Markdown 報告。

---

## 系統架構

```
使用者
  │ 描述研究任務
  ▼
ResearchPlannerAgent          ←→  SQLite DB（儲存/管理計畫）
  │ 與使用者共同制定研究計畫
  │ 輸出：最終研究計畫文字
  ▼
WebSearchAgent                ←→  Brave Search API（web + news）
  │ 用 Pydantic structured output 推導關鍵字與時效範圍
  │ 輸出：搜尋結果列表（url + description）
  ▼
SummaryReportAgent
  │ 彙整結果為 Markdown 報告（含來源連結）
  ▼
summary_report.md
```

---

## 技術亮點

| 設計決策 | 原因 |
|---|---|
| **三個 Agent 分工，而非單一 Agent** | 關注點分離：規劃、搜尋、摘要各有專責，更易維護與替換 |
| **Pydantic structured output** | 確保 LLM 回傳的搜尋參數格式正確，不依賴 prompt 解析 |
| **SQLite 保存研究計畫** | 使用者可跨對話管理多份研究計畫，不因 session 結束而遺失 |
| **Brave Search API** | 使用 freshness 參數，可明確設定搜尋結果時效範圍 |
| **Context Manager 資料庫連線** | 確保連線在任何情況下都能正確關閉，避免資源洩漏 |

---

## 快速開始

### 環境需求
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) 套件管理工具

### 安裝

```bash
git clone <your-repo-url>
cd <project-folder>
uv sync
```

### 設定環境變數

建立 `.env` 檔案：

```env
OPENAI_API_KEY=your_openai_api_key
BRAVE_API_KEY=your_brave_api_key
```

### 執行

```bash
uv run python main.py
```

### 操作流程

1. 程式啟動後描述你的研究任務（例如：「AI 在醫療診斷的最新應用」）
2. 與 Agent 對話，調整研究計畫的範圍與方向
3. 確認計畫後輸入 `accept`
4. 系統自動搜尋並整理，完成後在目錄產生 `summary_report.md`

---

## 設計思路

### 為什麼拆成三個 Agent？

單一 Agent 處理所有事情會導致 prompt 過長、職責混亂。三個 Agent 的設計讓每個環節都可以獨立優化——例如未來可以把 `WebSearchAgent` 換成 Perplexity API，或讓 `SummaryReportAgent` 輸出 PDF，而不影響其他部分。

### 為什麼用 Pydantic structured output？

搜尋需要精確的參數（關鍵字列表、時效代碼）。如果直接解析 LLM 的自然語言回覆，格式錯誤的機率很高。Pydantic 讓 LLM 的輸出有型別保障，大幅降低執行期錯誤。

---

## 已知限制與未來方向

**現有限制**
- 搜尋結果品質取決於 Brave API 的索引範圍
- LLM 摘要仍有幻覺風險，建議搭配原始連結人工驗證
- 目前為 CLI 工具，無 GUI

**未來 Roadmap**
- [ ] 加入來源可信度評分機制
- [ ] 支援匯出 PDF 格式報告
- [ ] 建立 Web UI（FastAPI + React）
- [ ] 支援多語言搜尋與報告

---

## 專案結構

```
.
├── main.py          # 三個 Agent 的定義與主程式邏輯
├── database.py      # SQLite 資料庫操作層
├── pyproject.toml   # 套件依賴（uv 管理）
├── .env             # 環境變數（不納入版控）
└── summary_report.md  # 執行後自動產生的報告
```