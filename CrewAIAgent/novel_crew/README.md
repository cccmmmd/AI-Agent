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

## 技術亮點

| 設計決策 | 原因 |
|---|---|
| **三個 Agent 分工，而非單一 Agent** | 關注點分離：創作、編輯、視覺各有專責，更易維護與替換 |
| **CrewAI sequential process** | 確保每個 Agent 的輸出自動成為下一個 Agent 的輸入，不需手動串接 |
| **自訂 BaseTool 封裝 OpenAI API** | 將 API 呼叫、base64 解碼、寫檔邏輯收斂到單一工具，Agent 只需傳入 prompt |
| **agents.yaml / tasks.yaml 分離設定** | Prompt 與程式邏輯解耦，調整角色或任務描述不需動到 Python 程式碼 |
| **只有插畫師掛載工具** | 作家與編輯不需要外部呼叫，明確限制工具使用範圍，降低非預期行為 |

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
├── crew.py              # Crew、Agent、Task 定義
├── config/
│   ├── agents.yaml      # 三個 Agent 的角色、目標與背景設定
│   └── tasks.yaml       # 三個 Task 的任務說明與期望輸出
└── tools/
    └── image_tool.py    # GenerateCoverImageTool（封面圖片生成）
```
