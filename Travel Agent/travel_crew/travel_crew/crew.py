"""
crew.py
-------
「專業導遊行前智庫」Crew 定義。

採用 CrewAI 標準 @CrewBase 架構：
  - Agent 定義來自 config/agents.yaml
  - Task  定義來自 config/tasks.yaml
  - tools/ 提供 Brave Search 工具
"""

import os
from typing import List
from functools import cached_property

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from travel_crew.tools.search_tools import (
    logistics_search,
    financial_search,
    safety_culture_search,
)


@CrewBase
class TravelGuideCrew:
    """
    專業導遊行前智庫 Crew。
    agents_config / tasks_config 指向 config/ 資料夾內的 YAML 檔。
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @cached_property
    def _llm(self):
        return LLM(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            temperature=0.3,
            api_key=os.environ.get("OPENAI_API_KEY", ""),
        )

    # ── Agents ────────────────────────────

    @agent
    def logistics_officer(self) -> Agent:
        """專業國際導遊專家：天氣 / 電力 / 飲水 / 網路"""
        return Agent(
            config=self.agents_config["logistics_officer"],  # type: ignore[index]
            tools=[logistics_search],
            llm=self._llm,
            max_iter=3,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def financial_advisor(self) -> Agent:
        """金融財務專家：匯率 / 換匯 / 刷卡 / 退稅"""
        return Agent(
            config=self.agents_config["financial_advisor"],  # type: ignore[index]
            tools=[financial_search],
            llm=self._llm,
            verbose=True,
            max_iter=3,
            allow_delegation=False,
        )

    @agent
    def safety_culture_expert(self) -> Agent:
        """文化與安全專家：詐騙 / 禁忌 / 禮儀 / 緊急電話"""
        return Agent(
            config=self.agents_config["safety_culture_expert"],  # type: ignore[index]
            tools=[safety_culture_search],
            llm=self._llm, 
            verbose=True,
            max_iter=3,
            allow_delegation=False,
        )

    @agent
    def lead_editor(self) -> Agent:
        """導遊文案主編：彙整所有素材，輸出 Markdown 報告"""
        return Agent(
            config=self.agents_config["lead_editor"],  # type: ignore[index]
            tools=[],
            llm=self._llm,
            verbose=True,
            max_iter=3,
            allow_delegation=True,
        )

    # ── Tasks ─────────────────────────────

    @task
    def logistics_task(self) -> Task:
        return Task(
            config=self.tasks_config["logistics_task"],  # type: ignore[index]
        )

    @task
    def financial_task(self) -> Task:
        return Task(
            config=self.tasks_config["financial_task"],  # type: ignore[index]
        )

    @task
    def safety_task(self) -> Task:
        return Task(
            config=self.tasks_config["safety_task"],  # type: ignore[index]
        )

    @task
    def final_report_task(self) -> Task:
        """主編整合任務：context 串接前三個 Task 的結果。"""
        return Task(
            config=self.tasks_config["final_report_task"],  # type: ignore[index]
            context=[
                self.logistics_task(),
                self.financial_task(),
                self.safety_task(),
            ],
            output_file="report.md",
        )

    # ── Crew ──────────────────────────────

    @crew
    def crew(self) -> Crew:
        """組建團隊，採循序執行確保主編拿到完整素材。"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
