from datetime import datetime
import json
import os
import sys
from typing import Dict, Any, List, Literal

# Run "uv sync" to install the below packages
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
import requests

import database

load_dotenv()

client = OpenAI()
database.init_db()

MAX_TOOL_CALL_ROUNDS = 5


class Tool:
    """
    所有工具的基底類別。
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
    ):
        self.name = name
        self.description = description
        self.parameters = parameters

    def get_schema(self) -> Dict[str, Any]:
        """
        回傳工具的 JSON Schema，供 OpenAI function calling 使用。
        """
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "additionalProperties": False,
                "required": list(self.parameters.keys()),
            },
        }

    def execute(self, arguments: str) -> str:
        """
        執行工具邏輯，子類別必須實作此方法。
        """
        raise NotImplementedError("每個工具必須實作自己的 execute 方法。")


class StoreResearchPlanTool(Tool):
    """
    將使用者的研究計畫儲存至資料庫的工具。
    """

    def __init__(self):
        super().__init__(
            name="store_research_plan",
            description="將使用者的研究計畫儲存至資料庫。",
            parameters={
                "short_summary": {
                    "type": "string",
                    "description": "研究計畫的簡短標題摘要。",
                },
                "details": {
                    "type": "string",
                    "description": "研究計畫的詳細內容。",
                },
            },
        )

    def execute(self, arguments: str) -> Dict[str, Any]:
        args = json.loads(arguments)
        try:
            result = database.add_research_plan(args["short_summary"], args["details"])
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}


class GetResearchPlansTool(Tool):
    """
    從資料庫取得使用者所有研究計畫的工具。
    """

    def __init__(self):
        super().__init__(
            name="get_research_plans",
            description="從資料庫取得使用者的所有研究計畫。",
            parameters={},
        )

    def execute(self, arguments: str) -> List[Dict[str, Any]]:
        try:
            return database.get_research_plans()
        except Exception as e:
            return [{"status": "error", "message": str(e)}]


class DeleteResearchPlanTool(Tool):
    """
    從資料庫刪除指定研究計畫的工具。
    """

    def __init__(self):
        super().__init__(
            name="delete_research_plan",
            description="從資料庫刪除使用者的指定研究計畫。",
            parameters={
                "id": {
                    "type": "integer",
                    "description": "欲刪除的研究計畫 ID。",
                },
            },
        )

    def execute(self, arguments: str) -> Dict[str, Any] | None:
        args = json.loads(arguments)
        try:
            result = database.delete_research_plan(args["id"])
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}


class Agent:
    """
    與 OpenAI API 互動的基底 Agent 類別。
    """

    def __init__(self, model: str = "gpt-4o"):
        self.client = client
        self.model = model
        self.messages: list[Dict[str, Any]] = []
        self.tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        """
        向 Agent 註冊一個工具。
        """
        self.tools[tool.name] = tool

    def _get_tool_schemas(self) -> list[Dict[str, Any]]:
        """
        回傳所有已註冊工具的 schema 列表。
        """
        return [tool.get_schema() for tool in self.tools.values()]

    def execute_tool_call(self, tool_call: Any) -> str:
        """
        執行工具呼叫並回傳結果。
        """
        fn_name = tool_call.name

        if fn_name in self.tools:
            tool_to_call = self.tools[fn_name]
            try:
                print(f"呼叫工具：{fn_name}，參數：{tool_call.arguments}")
                # 修復：移除未使用的 fn_args，直接傳入 arguments 字串
                return str(tool_to_call.execute(tool_call.arguments))
            except Exception as e:
                return f"呼叫 {fn_name} 時發生錯誤：{e}"

        return f"未知的工具：{fn_name}"

    def run(self):
        """
        執行 Agent，子類別必須實作此方法。
        """
        raise NotImplementedError("run 方法必須由子類別實作。")


class ResearchPlannerAgent(Agent):
    """
    協助使用者規劃研究計畫的 Agent。
    """

    def __init__(self):
        super().__init__()
        self.register_tool(StoreResearchPlanTool())
        self.register_tool(GetResearchPlansTool())
        self.register_tool(DeleteResearchPlanTool())
        self._set_initial_prompt()

    def _set_initial_prompt(self):
        self.messages = [
            {
                "role": "developer",
                "content": """
                你是一位研究計畫規劃助理，負責協助使用者規劃網路研究專案。
                使用者會提供一個研究任務，你的工作是與使用者共同制定一份完整的研究計畫。
                你的任務「不是」直接回答使用者的問題，而是協助他們建立一份優質的研究計畫，
                以便後續交由其他 Agent 執行。
                研究計畫應包含以下內容：
                    - 核心研究主題
                    - 相關延伸主題
                    - 應避免涉及的主題
                    - 網路搜尋的時間範圍（即搜尋結果的最大時效）
                請使用繁體中文與使用者溝通。
                """
            }
        ]

    def run(self):
        print("您好！請描述今天的研究任務：")
        while True:
            user_input = input("您的輸入（輸入 'exit' 離開，輸入 'accept' 確認研究計畫並繼續）：")
            if user_input == "exit":
                print("已離開。")
                sys.exit(0)
            elif user_input == "accept":
                print("研究計畫已確認，繼續執行...")
                prompt = "請產出最終版本的研究計畫，只回傳計畫本身，不需要其他說明或評論。"
                self.messages.append({"role": "user", "content": prompt})
                response = self.client.responses.create(
                    model=self.model,
                    input=self.messages,
                )
                print("以下是最終研究計畫：")
                print(response.output_text)
                return response.output_text

            self.messages.append({"role": "user", "content": user_input})

            for _ in range(MAX_TOOL_CALL_ROUNDS):
                response = self.client.responses.create(
                    model=self.model,
                    input=self.messages,
                    tools=self._get_tool_schemas(),
                )

                reply = response.output[0]
                self.messages.append(reply)

                if reply.type != "function_call":
                    print(response.output_text)
                    break

                tool_output = self.execute_tool_call(reply)
                self.messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": reply.call_id,
                        "output": tool_output,
                    }
                )


class SearchConfig(BaseModel):
    """
    搜尋設定的結構化輸出模型。
    """
    search_terms: list[str]
    freshness: Literal["pd", "pw", "pm", "py"] | str = Field(
        ...,
        description="網路搜尋結果的時效性。pd：過去一天，pw：過去一週，pm：過去一個月，py：過去一年。或指定時間範圍 YYYY-MM-DDtoYYYY-MM-DD（例如 2022-04-01to2022-07-30）"
    )


def _extract_search_results(api_response: dict, search_term: str) -> List[Dict[str, Any]]:
    """
    從 Brave API 回應中擷取 web 和 news 結果，消除重複邏輯。
    """
    results = []
    for section in ("web", "news"):
        if section in api_response:
            for item in api_response[section]["results"]:
                results.append({
                    "search_term": search_term,
                    "url": item["url"],
                    "description": item["description"],
                })
    return results


class WebSearchAgent(Agent):
    """
    根據研究計畫執行網路搜尋的 Agent。
    """

    def __init__(self):
        super().__init__()
        self._set_initial_prompt()
        # 提前檢查 API Key，避免執行到一半才報錯
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        if not self.brave_api_key:
            raise EnvironmentError("未設定 BRAVE_API_KEY 環境變數，請在 .env 檔案中設定。")

    def _set_initial_prompt(self):
        self.messages = [
            {
                "role": "developer",
                "content": f"""
                你是一位網路搜尋專家。
                你會收到一份研究計畫，並需要從中推導出一組搜尋關鍵字，用於執行網路搜尋。
                搜尋關鍵字應盡量具體且針對性強，以找到最相關的資訊。
                請專注於推導出有效且高影響力的關鍵字。

                同時請推導出網路搜尋結果的時效範圍（freshness）。
                今天的日期是：{datetime.now().strftime("%Y-%m-%d")}
                """
            }
        ]

    def run(self, research_plan: str) -> List[Dict[str, Any]]:
        print("正在推導搜尋關鍵字...")
        self.messages.append(
            {"role": "user", "content": "以下是研究計畫，請依此推導搜尋關鍵字：" + research_plan}
        )
        response = self.client.responses.parse(
            model=self.model,
            input=self.messages,
            text_format=SearchConfig,
        )

        search = response.output_parsed
        results = []

        for search_term in search.search_terms:
            api_response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.brave_api_key,
                },
                params={
                    "q": search_term,
                    "count": 10,
                    "freshness": search.freshness,
                },
            ).json()

            # 修復：抽出共用函式，消除 web/news 重複處理邏輯
            results.extend(_extract_search_results(api_response, search_term))

        return results


class SummaryReportAgent(Agent):
    """
    將搜尋結果整理成摘要報告的 Agent。
    """

    def __init__(self):
        super().__init__()
        self._set_initial_prompt()

    def _set_initial_prompt(self):
        self.messages = [
            {
                "role": "developer",
                "content": """
                你是一位摘要報告助理，請使用繁體中文撰寫報告。
                你會收到一組搜尋結果（包含簡短描述），請根據搜尋結果規劃符合「起承轉合」四個段落的報告，                
                需講述該段大綱與延伸內容要講什麼，必須在相關文字旁附上來源 URL，讓使用者可以深入閱讀。
                報告整體是一份易讀且實用的報告。
                報告格式為 Markdown，不需要額外的說明、注釋或其他文字，直接回傳 Markdown 報告即可。
                """
            }
        ]

    def run(self, search_results: list[Dict[str, Any]]) -> str:
        print("正在整理搜尋結果...")
        self.messages.append(
            {"role": "user", "content": "請根據以下搜尋結果產出摘要報告（請保留連結）：" + json.dumps(search_results, indent=2, ensure_ascii=False)}
        )
        response = self.client.responses.create(
            model=self.model,
            input=self.messages,
        )
        # 修復：改用 strip() 更安全地移除 markdown 包裝
        report = response.output_text.strip()
        if report.startswith("```markdown"):
            report = report[len("```markdown"):].strip()
        if report.endswith("```"):
            report = report[:-3].strip()
        return report


def main():
    agent = ResearchPlannerAgent()
    research_plan = agent.run()
    search_agent = WebSearchAgent()
    results = search_agent.run(research_plan)
    summary_report_agent = SummaryReportAgent()
    summary_report = summary_report_agent.run(results)

    with open("summary_report.md", "w", encoding="utf-8") as f:
        f.write(summary_report)

    print("報告已儲存至 summary_report.md")


if __name__ == "__main__":
    main()