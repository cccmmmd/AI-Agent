<img width="548" alt="image" src="https://github.com/user-attachments/assets/d16743aa-8bc1-46f0-ba41-625f628d61d2" />

# Novel Crew
> 由三個 Agent 協作，從「輸入主題」到「產出小說與封面」的全自動 AI 極短篇小說生成器。

---

## 這個專案想要解決

**創作極短篇小說需要反覆打磨**：構思故事、控制字數、潤飾文字、設計封面，每個環節都耗費心力。

這個專案把整個流程自動化：只需要用一句話描述小說主題，系統就會創作初稿、編輯潤飾，並用 AI 生成封面插圖，最終輸出一篇附有封面的極短篇小說。

---

## 系統架構

```
使用者
  │ 輸入小說主題
  ▼
writer（作家）
  │ {topic}
  │→ 根據主題創作初稿
  │→ 字數控制在 500 字以內，含標題
  │→ 回傳完整小說初稿
  ▼
editor（編輯）
  │ 初稿
  │→ 修正生硬或重複的用詞
  │→ 刪除冗餘段落，強化情感張力
  │→ 確保最終字數不超過 500 字
  │→ 輸出 novel.md
  ▼
illustrator（插畫師）                ←→  OpenAI gpt-image-1
  │ 潤飾稿
  │→ 分析小說核心意象與情感氛圍
  │→ 撰寫 50–80 字英文 image prompt
  │→ 呼叫 GenerateCoverImageTool
  │→ 輸出 cover.png（1024×1024）
```

---

## 關於 Prompt 的幾個設計決策

**1. Backstory 是在幫 LLM 建立一個「會這樣輸出」的角色**

writer 的 backstory 沒有只說「你是作家」，而是寫了：
> 你善於在極短的篇幅內建立完整的敘事弧，讓每個字都充滿力量。你的作品常常以意想不到的結局或意象收尾。

這不是裝飾文字，是在告訴 LLM「輸出風格要長這樣」。具體的描述比抽象的頭銜更有效——「意想不到的結局」比「寫得好」更能影響生成方向。

illustrator 的 backstory 裡特別加了一句：「你精通 AI 圖像生成的 prompt，能用精煉的英文描述喚起強烈的視覺感受。」這是刻意的——沒有這句話，LLM 可能輸出一段中文場景描述，然後你就沒辦法直接餵給圖像模型。

**2. 負向約束比正向描述更重要**

task description 裡有幾句話看起來很多餘，其實很關鍵：
> 不需要任何說明或前言，直接輸出小說內容。
> 請輸出修改後的繁體中文完整小說，不需附上修改說明。

LLM 的預設行為是「會解釋自己在做什麼」。如果不明確禁止，editor 可能輸出「以下是修改後的版本，我主要做了 XXX 調整……」，這些文字最後會一起寫進 novel.md，破壞輸出品質。負向約束的作用就是把這個預設行為關掉。

**3. illustration task 的格式規格決定圖片品質**

任務描述裡指定了 image prompt 的組成要素：
> 需包含：畫面主體、構圖方式、色彩風格、藝術媒介、氛圍關鍵字。（50–80 字）

這讓 illustrator 輸出的不是「一個孤獨的人站在月台」，而是類似：
> A solitary figure on a misty train platform at dusk, wide-angle cinematic composition, muted blue-grey palette, watercolor illustration, melancholic and quiet atmosphere.

同樣是描述同一個場景，後者生成出來的圖會好非常多。

**4. 只有插畫師有工具掛載**

writer 和 editor 不需要任何外部呼叫，給他們工具只會增加誤觸的機率。只有 illustrator 掛了 `GenerateCoverImageTool`，明確限制工具使用範圍。

Tool 本身把「呼叫 API → base64 解碼 → 寫檔」三步封裝進去，Agent 只需要傳一個 prompt 字串，不需要知道 API 的任何細節。

---

## 快速開始

### 環境需求

- Python 3.10+
- [CrewAI](https://docs.crewai.com)
- OpenAI API 金鑰

### 安裝

```bash
pip install crewai openai
```

### 設定環境變數

```bash
export OPENAI_API_KEY=sk-...
```

CrewAI 預設使用 `OPENAI_API_KEY` 作為 LLM。若需改用其他模型，請參考 [CrewAI LLM 設定文件](https://docs.crewai.com/concepts/llms)。

### 執行

```bash
cd novel_crew
python main.py
```

### 操作流程

1. 程式啟動後輸入小說主題（例如：「在月台上等不到的那班車」）
2. 系統依序由作家、編輯、插畫師自動處理
3. 完成後在當前目錄產生 `novel.md` 與 `cover.png`

---

## 設計思路

### 拆成三個 Agent

單一 Agent 同時負責創作、潤飾、繪圖，會導致 prompt 過長、職責混亂。三個 Agent 的設計讓每個環節可以獨立優化——例如未來可以換掉插畫師的圖像模型，或讓編輯 Agent 加入字數統計工具，而不影響其他部分。

### 用自訂 Tool 封裝圖像 API

如果讓插畫師 Agent 直接輸出 image prompt 文字，就需要額外的程式去呼叫 API 並寫檔。`GenerateCoverImageTool` 把這三步收進一個工具：

```python
# Agent 只需要這樣呼叫
generate_cover_image(prompt="...")

# Tool 內部處理
response = client.images.generate(model="gpt-image-1", prompt=prompt, ...)
image_bytes = base64.b64decode(response.data[0].b64_json)
open("cover.png", "wb").write(image_bytes)
```

Agent 不需要知道 API 細節，Tool 換掉模型也不影響 Agent 的行為。

---

## 專案結構

```
novel_crew/
├── main.py              # 入口點，提示輸入主題並啟動 Crew
├── crew.py              # Crew、Agent、Task 的組裝邏輯
├── config/
│   ├── agents.yaml      # 三個 Agent 的角色、目標與背景設定
│   └── tasks.yaml       # 三個 Task 的任務說明與期望輸出
└── tools/
    └── image_tool.py    # GenerateCoverImageTool（封面圖片生成）
```
