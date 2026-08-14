"""Single-agent brain (optimized for speed)."""

from __future__ import annotations

import logging
import re

from crewai import Agent, Crew, Process, Task

from algoforge.brain import prompts
from algoforge.brain.llm import build_llm
from algoforge.config import Settings, get_settings
from algoforge.models import ForgeResult, Problem

log = logging.getLogger(__name__)


def _extract_solutions(text: str) -> dict[str, str]:
    """Extract Python and Java code from markdown fences."""
    text = (text or "").strip()
    solutions = {}
    
    py_match = re.search(r"```(?:python3?|py)\s*\n([\s\S]*?)```", text, re.IGNORECASE)
    if py_match:
        solutions["python"] = py_match.group(1).strip()
        
    java_match = re.search(r"```java\s*\n([\s\S]*?)```", text, re.IGNORECASE)
    if java_match:
        solutions["java"] = java_match.group(1).strip()
        
    if not solutions:
        raise ValueError(
            "Failed to extract code from the agent's markdown response. "
            "The model did not output valid code fences. Pipeline halted."
        )
    return solutions


def _task_text(task: Task) -> str:
    out = task.output
    if out is None:
        return ""
    raw = getattr(out, "raw", None)
    return str(raw if raw is not None else out)


def run_brain(problem: Problem, settings: Settings | None = None) -> ForgeResult:
    """Kick off the optimized single-pass Master Agent and return structured artifacts."""
    settings = settings or get_settings()
    log.info("Assembling optimized single-pass Master Agent...")
    llm = build_llm(settings)

    master_agent = Agent(
        role="Principal Staff Engineer & Mentor",
        goal="Solve the algorithm problem optimally and produce a teaching README with real-world examples.",
        backstory=prompts.MASTER_BACKSTORY,
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    master_task = Task(
        description=prompts.MASTER_TASK,
        expected_output="A single, complete Markdown README containing the intuition, Python solution, and examples.",
        agent=master_agent,
    )

    crew = Crew(
        agents=[master_agent],
        tasks=[master_task],
        process=Process.sequential,
        verbose=True,
    )

    log.info(f"Forging optimized single-pass solution for: {problem.title}")
    crew.kickoff(
        inputs={
            **problem.crew_inputs(),
            "leetcode_username": settings.leetcode_username,
        }
    )

    readme = _task_text(master_task).strip()
    solutions = _extract_solutions(readme)

    log.info("Agent finished — solution + teaching notes ready.")
    return ForgeResult(problem=problem, solutions=solutions, readme_markdown=readme)
