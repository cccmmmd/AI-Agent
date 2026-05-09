#!/usr/bin/env python
import sys
import warnings

from novel_crew.crew import NovelCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    執行極短篇小說創作 Crew。
    """
    topic = input("請輸入小說主題：")
    inputs = {
        'topic': topic,
    }

    try:
        NovelCrew().crew().kickoff(inputs=inputs)
        print("\n 小說已生成完畢，請查看 novel.md 檔案。")
    except Exception as e:
        raise Exception(f"執行時發生錯誤：{e}")


def train():
    """
    訓練 Crew。
    """
    inputs = {"topic": "孤獨"}
    try:
        NovelCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"訓練時發生錯誤：{e}")


def replay():
    """
    重播指定任務的執行過程。
    """
    try:
        NovelCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"重播時發生錯誤：{e}")


def test():
    """
    測試 Crew 執行並回傳結果。
    """
    inputs = {"topic": "孤獨"}
    try:
        NovelCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"測試時發生錯誤：{e}")
