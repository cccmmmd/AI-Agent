<img width="548" alt="image" src="https://github.com/user-attachments/assets/ba36f24a-514f-45a2-98c9-47bfc70ce6b0" />


# Research Planner Agent — AI 研究報告助手

> 未使用任何Agent套件，純 Python 打造三個 Agent 協作，從「提出問題」到「產出報告」的全自動 AI 研究報告助手。

---

## 這個專案想要解決

**手動研究太耗時**：找資料、篩關鍵字、整理來源、撰寫摘要，這些步驟加起來往往要花數小時。

這個專案從零開始不靠任何 Agent 框架，實作一套流程自動化系統：只用一句話描述研究主題，系統就會規劃研究方向、搜尋網路、整理成一份附有來源連結的 Markdown 報告。 我也藉此有機會弄清楚框架底層在做什麼：包含 function calling 串接、structured output 怎麼用、工具怎麼設計得讓 LLM 容易理解

## 系統架構

```
使用者
  │ 描述研究任務
  ▼
ResearchPlannerAgent          ←→  SQLite DB（儲存/管理計畫）
  │ 使用者描述研究主題
  │→ LLM 進行多輪對話，協助使用者收斂研究計畫
  │→ 可呼叫工具將計畫存入 / 取出 / 刪除資料庫
  │→ 使用者輸入 'accept' 後
  │→ 要求 LLM 產出最終版研究計畫文字並回傳
  ▼
WebSearchAgent                ←→  Brave Search API（web + news）
  │ 研究計畫文字
  │→ LLM 用 structured output（pydantic）解析出：
  │   - search_terms（搜尋關鍵字列表）
  │   - freshness（時間範圍，如 pw=過去一週）
  │→ 對每個關鍵字呼叫 Brave Search API
  │→ 蒐集 web + news 結果（url + description）
  │→ 回傳結果列表
  ▼
SummaryReportAgent
  │ 搜尋結果列表（JSON）
  │→ 傳給 LLM 摘要整理
  │→ 去除多餘的 ```markdown 包裝
  │→ 回傳乾淨的 Markdown 字串
  ▼
summary_report.md
```

---

## 關於 Prompt 的幾個設計決策

**1. ResearchPlannerAgent 的角色限定：「你的工作不是回答問題」**

這是整個系統最重要的一句 prompt：
> 你的任務「不是」直接回答使用者的問題，而是協助他們建立一份優質的研究計畫。

LLM 的預設行為就是「把問題回答掉」。使用者說「我想研究 AI 在醫療的應用」，沒有這個約束的話，Agent 很可能直接開始列知識點。加了這句話之後，它才會開始問使用者「你想聚焦在哪個科別？時間範圍要多近期？」

同時 system prompt 裡列出了研究計畫應該包含的四個要素（核心主題、延伸主題、排除主題、時間範圍），讓 Agent 知道「好的計畫長什麼樣子」，引導方向而不只是亂問問題。

**2. accept 之後的二段式設計**

使用者輸入 `accept` 確認計畫後，系統不是直接把對話歷史傳給下一個 Agent，而是先多問一次：
> 請產出最終版本的研究計畫，只回傳計畫本身，不需要其他說明或評論。

這一步的作用是讓 LLM 從「對話模式」切換到「輸出模式」，產出一份乾淨可用的文字，而不是夾雜著「好的，根據我們的討論……」這類確認語句。下游 Agent 拿到的是直接可以用的輸入，不需要再做清理。

**3. 用 Pydantic structured output 固定搜尋參數格式**

WebSearchAgent 拿到研究計畫之後，需要把它轉成 Brave Search API 可以接受的格式：關鍵字列表 + freshness 代碼（`pw` = 過去一週，`pm` = 過去一個月……）。

如果用自然語言讓 LLM 輸出再自己解析，格式很容易出錯。我用 Pydantic 定義 `SearchConfig`，透過 `client.responses.parse()` 讓 LLM 直接回傳型別正確的物件：

```python
class SearchConfig(BaseModel):
    search_terms: list[str]
    freshness: Literal["pd", "pw", "pm", "py"] | str

search.search_terms  # ["AI 醫療診斷", "深度學習 病理影像"]
search.freshness     # "pm"
```

拿到就能直接用，不需要寫任何解析邏輯，也不會因為 LLM 改變輸出格式就壞掉。

**4. WebSearchAgent 注入當天日期**

system prompt 裡動態注入 `datetime.now()`：
> 今天的日期是：2026-05-14

這讓 LLM 在判斷 freshness 時有時間錨點。沒有這個，「過去一個月」對 LLM 來說是模糊的，容易做出不合理的時效判斷。一行程式碼，讓搜尋結果準確很多。

**5. SummaryReportAgent 的防禦性清理**

system prompt 已經說了「直接回傳 Markdown，不需要其他文字」，但 LLM 有時還是會在外層包 ` ```markdown ` 代碼區塊。所以在程式層面加了清理：

```python
report = response.output_text.strip()
if report.startswith("```markdown"):
    report = report[len("```markdown"):].strip()
```

Prompt 說得再清楚，都需要在程式層加一道防禦！

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

1. 程式啟動後描述研究任務（例如：「AI 在醫療診斷的最新應用」）
2. 與 Agent 對話，調整研究計畫的範圍與方向
3. 確認計畫後輸入 `accept`
4. 系統自動搜尋並整理，完成後在目錄產生 `summary_report.md`

---

## 設計思路

### 拆成三個 Agent

單一 Agent 處理所有事情會導致 prompt 過長、職責混亂。三個 Agent 的設計讓每個環節都可以獨立優化——例如未來可以把 `WebSearchAgent` 換成 Perplexity API，或讓 `SummaryReportAgent` 輸出 PDF，而不影響其他部分。

### 用 Pydantic 把輸出結構化

搜尋需要精確的參數（關鍵字列表、時效代碼）。如果直接解析 LLM 的自然語言回覆，格式錯誤的機率很高。Pydantic 讓 LLM 的輸出有型別保障，大幅降低執行期錯誤。
如果不用 structured output，LLM 可能回傳：
```
搜尋關鍵字：AI 醫療、深度學習診斷...
時效：過去一個月
```
我還需要自己寫解析邏輯，格式一旦變化就壞掉。用 `SearchConfig` 之後，拿到的直接是：
```python
search.search_terms  # ["AI 醫療", "深度學習診斷"]
search.freshness     # "pm"
```
型別正確、可直接使用，不需要額外處理。

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
