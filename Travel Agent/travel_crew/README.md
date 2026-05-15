# Travel Crew － 旅遊顧問
> 由四個 Agent 協作，從「輸入目的地」到「產出行前報告」的全自動 AI 旅遊顧問。

---

## 這個專案想要解決

**出發前要查的東西又多又雜，** 讓人焦慮！天氣、插座、換匯、詐騙手法、文化禁忌……每件事都要花時間搜尋、理解、紀錄，最後想拼成一份有用的文件更花心神。

這個專案把整個流程自動化：只需要輸入目的地、出發日期、旅客類型，三位領域專家 Agent 會同時展開調查，最後由主編 Agent 整合成一份針對該客群的完整 Markdown 行前報告。

---

## 系統架構

```
使用者
  │ 輸入 destination / date / customer_type
  │
  ├──→ logistics_officer（導遊專家）     ←→  Brave Search API
  │      │→ 天氣、電力插座、飲水安全、行動網路
  │
  ├──→ financial_advisor（金融顧問）     ←→  Brave Search API
  │      │→ 匯率、換匯建議、刷卡普及度、退稅流程
  │
  └──→ safety_culture_expert（文化安全專家）  ←→  Brave Search API
         │→ 詐騙手法、文化禁忌、宗教禮儀、緊急聯絡
         │
         ▼（三份調查結果同時傳入）
      lead_editor（主編）
         │→ 整合三份素材
         │→ 依 customer_type 調整語氣與重點
         │→ 輸出 Markdown 行前報告
         ▼
      reports/行前報告_{目的地}_{日期}_{timestamp}.md
```

前三個 Agent 各自調查自己的領域，`final_report_task` 透過 `context` 參數同時拿到三份結果，再由主編統一整合輸出。

---

## 關於 Prompt 的幾個設計決策

**1. Backstory 裡放具體細節，決定輸出的精度**

`logistics_officer` 的 backstory 沒有只說「你是有經驗的導遊」，而是：
> 你清楚知道義大利的插座是 Type L、羅馬十月會下雨的機率，以及哪些國家的自來水其實能喝。你說話簡潔、條列清晰，絕不廢話。

「義大利的插座是 Type L」這個細節在告訴 LLM「輸出應該精確到這個粒度」。「絕不廢話」是風格約束，防止輸出一堆沒用的鋪陳。

`financial_advisor` 的 backstory 結尾：「你給的建議永遠具體到『幾塊錢』，不說廢話。」效果一樣——不說「建議帶足夠的現金」，而是「建議帶約 5,000 日圓現金備用」，這個粒度差異就是 backstory 帶出來的。

**2. 三個調查 Task 都有同一句負向約束**

```
請勿涉及任何交通運輸、航班或路線規劃。
```

旅遊搜尋很容易帶出交通資訊。這句話刻意重複出現在三個 Task 裡——如果任何一個 Agent 輸出了交通建議，主編整合時可能把它放進報告，但這個系統設計上不負責交通規劃，讓使用者誤以為可信反而是問題。

**3. `{customer_type}` 讓同一個目的地產出不同內容**

三個調查 Task 都把 `{customer_type}` 放進 description，透過 `kickoff(inputs=...)` 注入。同樣是「羅馬的詐騙手法」，對銀髮樂齡團的建議會強調「不要被街頭藝人圍住、不輕易接受免費贈品」，對學生背包客則會強調「寄物置物的風險、假警察查護照」——同一套系統、同一個目的地，因為 `customer_type` 不同，輸出的重點就不一樣。

**4. 主編的 task description 把格式規格寫死，不留空間給 LLM 自由發揮**

```
格式要求（Markdown）：
1. 開頭以溫暖的導遊口吻寫一段「行前歡迎辭」（3-4 句）
2. 章節結構依序：天氣與行李準備 / 電力與網路設備 /
   飲食與飲水安全 / 金融與消費指南 / 安全防護盾 /
   文化禮儀與禁忌 / 緊急聯絡一覽 /
   行李準備 Checklist（checkbox 格式）/ 導遊的小叮嚀（2-3 條）
3. 語氣：資深管家風格，專業但不冷冰冰
4. 每個章節使用粗體小標、條列或表格，確保手機也易讀
5. 嚴格排除任何交通運輸、航班資訊或路線規劃
```

「checkbox 格式」特別指定，讓 Checklist 輸出 `- [ ] 帶轉接頭` 而不是普通列表。「3-4 句」、「2-3 條」這類數字是為了避免 LLM 把歡迎辭寫成一篇文章。章節名稱和順序全部鎖定，確保每次產出的結構穩定一致。

**5. 工具的 docstring 就是 prompt，裡面放輸入範例**

三個搜尋工具底層都呼叫同一個 `_brave_search()`，但各自有不同的 docstring：

```python
@tool("logistics_search")
def logistics_search(query: str) -> str:
    """
    搜尋天氣預報、電壓插座規格、飲水安全與行動網路覆蓋率。
    輸入範例："Rome October weather forecast" 或 "Italy plug type voltage"
    """
```

LLM 根據 docstring 決定怎麼用這個工具。「輸入範例」讓它知道 query 應該是精煉的英文搜尋字串，而不是完整的中文句子——搜尋品質直接影響報告品質，這個細節很關鍵。

---

## 快速開始

### 環境需求

- Python 3.10–3.13
- [uv](https://github.com/astral-sh/uv) 套件管理工具
- OpenAI API 金鑰
- Brave Search API 金鑰

### 安裝

```bash
cd "Travel Agent/travel_crew"
uv sync
```

### 設定環境變數

建立 `.env` 檔案：

```env
OPENAI_API_KEY=your_openai_api_key
BRAVE_API_KEY=your_brave_api_key
OPENAI_MODEL=gpt-4o-mini    # 可選，預設 gpt-4o-mini
```

### 執行

```bash
uv run travel_crew
```

### 操作流程

1. 程式啟動後輸入旅遊目的地（例如：`義大利 羅馬`）
2. 輸入出發日期（例如：`2026年10月`）
3. 從選單選擇客戶類型
4. 系統自動完成搜尋與整合，在 `reports/` 目錄產生帶有 timestamp 的行前報告

---

## 設計思路

### 為什麼主編用 `context` 而不靠 Sequential 自動傳遞

前三個 Task 是平行關係——天氣、財務、安全三份調查互相獨立，沒有誰依賴誰。如果只靠 Sequential Process 的自動傳遞，主編只會拿到「上一個 Task 的輸出」，前兩份調查結果就丟了。

`context` 參數讓三份素材同時進入主編的 context window：

```python
def final_report_task(self) -> Task:
    return Task(
        config=self.tasks_config["final_report_task"],
        context=[
            self.logistics_task(),
            self.financial_task(),
            self.safety_task(),
        ],
        output_file="report.md",
    )
```

### 三個工具分開定義，底層共用

`search_tools.py` 定義了三個獨立的 `@tool`，底層都呼叫同一個 `_brave_search()`。分開定義的原因不是功能不同，而是 **docstring 不同**——LLM 根據 description 決定「這個工具該用來查什麼」，分開定義讓財務 Agent 不會拿著財務工具去查天氣，語意邊界清楚。

### `temperature=0.3`，調查類任務要的是準確不是創意

所有 Agent 共用同一個 LLM 設定，透過 `lru_cache` 確保只建立一個實例。temperature 設 0.3，讓調查 Agent 的輸出偏向穩定、可重現，不會每次查同一個目的地給出差異很大的建議。

---

## 專案結構

```
travel_crew/
├── main.py                   # 入口點、使用者輸入、報告存檔邏輯
├── crew.py                   # TravelGuideCrew 定義：四個 Agent 與四個 Task 的組裝
├── config/
│   ├── agents.yaml           # 四個 Agent 的 role、goal、backstory
│   └── tasks.yaml            # 四個 Task 的 description 與 expected_output
└── tools/
    └── search_tools.py       # 三個搜尋工具（共用 _brave_search 底層）
```
