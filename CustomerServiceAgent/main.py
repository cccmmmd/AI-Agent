import json
import sqlite3
from datetime import datetime
from typing import Dict, Any

# Run "uv sync" to install the below packages
from dotenv import load_dotenv
from openai import OpenAI

from database import create_db_and_tables

load_dotenv()

client = OpenAI()

DB_FILE = "dummy_database.db"
MAX_TOOL_CALL_ROUNDS = 5

create_db_and_tables()


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


class VerifyCustomerTool(Tool):
    def __init__(self):
        super().__init__(
            name="verify_customer",
            description="使用客戶的全名和 PIN 碼驗證其身份。",
            parameters={
                "name": {
                    "type": "string",
                    "description": "客戶的全名，例如：'John Doe'。",
                },
                "pin": {"type": "string", "description": "客戶的 PIN 碼。"},
            },
        )

    def execute(self, arguments: str) -> str:
        try:
            args = json.loads(arguments)
            parts = args["name"].lower().split()
            if len(parts) < 2:
                return str(-1)
            first_name, last_name = parts[0], parts[-1]
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM customers WHERE LOWER(first_name) = ? AND LOWER(last_name) = ? AND pin = ?",
                    (first_name, last_name, args["pin"]),
                )
                result = cursor.fetchone()
            if result:
                return str(result[0])
            return str(-1)
        except Exception as e:
            return f"執行 {self.name} 時發生錯誤：{e}"


class GetOrdersTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_orders",
            description="取得已驗證客戶的訂單歷史紀錄。",
            parameters={
                "customer_id": {
                    "type": "integer",
                    "description": "客戶的唯一識別碼。",
                }
            },
        )

    def execute(self, arguments: str) -> str:
        try:
            args = json.loads(arguments)
            with sqlite3.connect(DB_FILE) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM orders WHERE customer_id = ?", (args["customer_id"],)
                )
                orders = [dict(row) for row in cursor.fetchall()]
            return json.dumps(orders)
        except Exception as e:
            return f"執行 {self.name} 時發生錯誤：{e}"


class CheckRefundEligibilityTool(Tool):
    def __init__(self):
        super().__init__(
            name="check_refund_eligibility",
            description="根據訂單日期檢查訂單是否符合退款資格。",
            parameters={
                "customer_id": {
                    "type": "integer",
                    "description": "客戶的唯一識別碼。",
                },
                "order_id": {
                    "type": "integer",
                    "description": "訂單的唯一識別碼。",
                },
            },
        )

    def execute(self, arguments: str) -> str:
        try:
            args = json.loads(arguments)
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT date FROM orders WHERE id = ? AND customer_id = ?",
                    (args["order_id"], args["customer_id"]),
                )
                result = cursor.fetchone()
            if not result:
                return str(False)
            order_date = datetime.fromisoformat(result[0])
            return str((datetime.now() - order_date).days <= 30)
        except Exception as e:
            return f"執行 {self.name} 時發生錯誤：{e}"


class IssueRefundTool(Tool):
    def __init__(self):
        super().__init__(
            name="issue_refund",
            description="為訂單執行退款。",
            parameters={
                "customer_id": {
                    "type": "integer",
                    "description": "客戶的唯一識別碼。",
                },
                "order_id": {
                    "type": "integer",
                    "description": "訂單的唯一識別碼。",
                },
            },
        )

    def execute(self, arguments: str) -> str:
        try:
            args = json.loads(arguments)
            # 實際應用中，這裡應將退款紀錄寫入資料庫
            print(
                f"已為客戶 {args['customer_id']} 的訂單 {args['order_id']} 執行退款。"
            )
            return str(True)
        except Exception as e:
            return f"執行 {self.name} 時發生錯誤：{e}"


class ShareFeedbackTool(Tool):
    def __init__(self):
        super().__init__(
            name="share_feedback",
            description="讓客戶提供使用體驗的回饋。",
            parameters={
                "customer_id": {
                    "type": "integer",
                    "description": "客戶的唯一識別碼。",
                },
                "feedback": {
                    "type": "string",
                    "description": "客戶提供的回饋內容。",
                },
            },
        )

    def execute(self, arguments: str) -> str:
        try:
            args = json.loads(arguments)
            # 實際應用中，這裡應將回饋儲存至資料庫
            print(
                f"收到客戶 {args['customer_id']} 的回饋：{args['feedback']}"
            )
            return "感謝您的回饋！"
        except Exception as e:
            return f"執行 {self.name} 時發生錯誤：{e}"


class Agent:
    """
    與 OpenAI API 互動的基底 Agent 類別。
    """

    def __init__(self, model: str = "gpt-4o"):
        self.client = OpenAI()
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
                # 修復：傳入 arguments 字串，而非整個 tool_call 物件
                return str(tool_to_call.execute(tool_call.arguments))
            except Exception as e:
                return f"呼叫 {fn_name} 時發生錯誤：{e}"

        return f"未知的工具：{fn_name}"

    def run(self):
        """
        執行 Agent，子類別必須實作此方法。
        """
        raise NotImplementedError("run 方法必須由子類別實作。")


class CustomerServiceAgent(Agent):
    """
    繼承 Agent 基底類別的客服 Agent。
    """

    def __init__(self, model="gpt-4o"):
        super().__init__(model)
        self._set_initial_prompt()
        self._register_all_tools()

    def _set_initial_prompt(self):
        self.messages = [
            {
                "role": "developer",
                "content": """
                    你是一位親切且專業的客服人員，請使用繁體中文與客戶溝通。
                    你必須「先驗證客戶身份」，才能提供任何敏感資訊。
                    在身份驗證完成前，你「絕對不可以」向客戶透露任何資訊。
                    你「只能」回答與客戶服務相關的問題，不得提供無關資訊。
                    「不要」猜測任何資訊，包含客戶資料、訂單資料或其他任何事項。
                    若無法協助客戶完成某項任務，請引導客戶聯繫人工客服。
                    執行任何重要操作前，請務必向客戶確認。
                    若客戶詢問與客服無關的事項，你必須回覆：「很抱歉，這個問題超出我的服務範圍，我無法協助您。」
                """
            }
        ]

    def _register_all_tools(self):
        tools_to_register = [
            VerifyCustomerTool(),
            GetOrdersTool(),
            CheckRefundEligibilityTool(),
            IssueRefundTool(),
            ShareFeedbackTool(),
        ]

        for tool in tools_to_register:
            self.register_tool(tool)

    def run(self):
        """
        執行 Agent 的主要互動迴圈。
        """
        print(
            "歡迎使用客服聊天機器人！請問有什麼可以協助您的？輸入 'exit' 可結束對話。"
        )
        while True:
            user_input = input("您的輸入：")
            if user_input.lower() == "exit":
                break

            self.messages.append({"role": "user", "content": user_input})

            for _ in range(MAX_TOOL_CALL_ROUNDS):
                response = self.client.responses.create(
                    model=self.model,
                    input=self.messages,
                    tools=self._get_tool_schemas(),
                )

                output = response.output

                for reply in output:
                    self.messages.append(reply.model_dump())

                    if reply.type != "function_call":
                        print(reply.content[0].text)
                    else:
                        fn_name = reply.name
                        if fn_name in self.tools:
                            tool_to_call = self.tools[fn_name]
                            tool_output = tool_to_call.execute(reply.arguments)
                        else:
                            tool_output = f"未知的工具：{fn_name}"

                        self.messages.append(
                            {
                                "type": "function_call_output",
                                "call_id": reply.call_id,
                                "output": tool_output,
                            }
                        )

                # 改為判斷本輪 output 中是否還有待處理的 function_call
                has_pending_tool_call = any(reply.type == "function_call" for reply in output)
                if not has_pending_tool_call:
                    break


def main():
    agent = CustomerServiceAgent()
    agent.run()


if __name__ == "__main__":
    main()