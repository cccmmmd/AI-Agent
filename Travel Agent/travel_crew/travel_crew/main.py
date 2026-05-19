#!/usr/bin/env python
"""
main.py
-------
「專業導遊行前智庫」主程式入口。

"""

import sys
import warnings
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from travel_crew.crew import TravelGuideCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# 載入 .env（OPENAI_API_KEY、BRAVE_API_KEY、OPENAI_MODEL）
load_dotenv()

# ── 輸出目錄 ──────────────────────────────
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


# ══════════════════════════════════════════
#  工具函式
# ══════════════════════════════════════════

def build_filename(destination: str, date: str) -> str:
    safe_dest = re.sub(r"[^\w\u4e00-\u9fff]", "_", destination)
    safe_date = re.sub(r"[^\w]", "_", date)
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M")
    return f"行前報告_{safe_dest}_{safe_date}_{timestamp}.md"


def save_report(content: str, filename: str) -> Path:
    filepath = REPORTS_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def _kickoff_and_save(inputs: dict) -> None:
    """
    統一的執行 + 儲存邏輯，供 run() 與 main() 共用。
    報告統一以帶時間戳的動態檔名存入 reports/ 資料夾。
    """
    result = TravelGuideCrew().crew().kickoff(inputs=inputs)
    report_content = str(result)

    filename = build_filename(inputs["destination"], inputs["date"])
    filepath = save_report(report_content, filename)

    print("\n" + "=" * 55)
    print(" 報告產出完成！")
    print(f" 檔案位置：{filepath.resolve()}")
    print("=" * 55 + "\n")
    print(report_content)


# ══════════════════════════════════════════
#  crewAI 標準函式（供 crewai run / train 使用）
# ══════════════════════════════════════════

def get_user_inputs():
    """統一獲取使用者輸入的邏輯"""
    print("\n" + "請提供訓練/執行參數")
    print("=" * 55)

    # 目的地
    destination = input("\n請輸入旅遊目的地，國家 城市（例：日本 東京）：").strip() or "日本 東京"

    # 日期
    date = input("\n📅 請輸入出發日期（例：2026年8月）：").strip() or "2026年4月"

    # 客戶類型
    customer_options = {
        "1": "高級商務考察團",
        "2": "親子家庭團",
        "3": "銀髮樂齡團",
        "4": "蜜月情侶",
        "5": "學生背包客",
    }
    print("\n👥 請選擇客戶類型：")
    for key, val in customer_options.items():
        print(f"   {key}. {val}")

    choice = input("\n   請輸入編號（預設 1）：").strip()
    customer_type = customer_options.get(choice, customer_options["1"])

    return {
        "destination": destination,
        "date": date,
        "customer_type": customer_type,
    }


def run():
    """供 crewai run 指令使用。"""
    inputs = get_user_inputs()
    try:
        _kickoff_and_save(inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """Train the crew for a given number of iterations."""
    inputs = get_user_inputs()
    try:
        TravelGuideCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """Replay the crew execution from a specific task."""
    try:
        TravelGuideCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """Test the crew execution and returns the results."""
    inputs = get_user_inputs()
    try:
        TravelGuideCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


# ══════════════════════════════════════════
#  CLI 入口（直接 python main.py 執行）
# ══════════════════════════════════════════

def main():
    inputs = get_user_inputs()
    try:
        _kickoff_and_save(inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


if __name__ == "__main__":
    main()
