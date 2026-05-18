from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from novel_crew.tools.image_tool import GenerateCoverImageTool


@CrewBase
class NovelCrew():
    """極短篇小說創作 Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config['writer'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def editor(self) -> Agent:
        return Agent(
            config=self.agents_config['editor'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def illustrator(self) -> Agent:
        return Agent(
            config=self.agents_config['illustrator'],  # type: ignore[index]
            verbose=True,
            tools=[GenerateCoverImageTool()]
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config['writing_task'],  # type: ignore[index]
        )

    @task
    def editing_task(self) -> Task:
        return Task(
            config=self.tasks_config['editing_task'],  # type: ignore[index]
        )

    @task
    def illustration_task(self) -> Task:
        return Task(
            config=self.tasks_config['illustration_task'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """建立極短篇小說創作 Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
