"""Domain models shared across ingestion → brain → committer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodeSnippet:
    lang: str
    lang_slug: str
    code: str


@dataclass
class Problem:
    """Normalized problem payload for the agent pipeline."""

    source: str  # leetcode | codeforces
    problem_id: str
    title: str
    difficulty: str
    date: str
    url: str
    topics: list[str] = field(default_factory=list)
    description_html: str = ""
    description_text: str = ""
    templates: dict[str, str] = field(default_factory=dict)
    snippets: list[CodeSnippet] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def title_slug(self) -> str:
        slug = (self.extra or {}).get("title_slug")
        if slug:
            return str(slug)
        # Fallback: kebab-case from title, stripping unsafe chars
        import re
        cleaned = self.title.strip().lower()
        cleaned = re.sub(r"[^a-z0-9\s-]", "", cleaned)  # strip special chars
        cleaned = re.sub(r"[\s_]+", "-", cleaned)  # spaces/underscores to hyphens
        cleaned = re.sub(r"-{2,}", "-", cleaned)  # collapse multiple hyphens
        return cleaned.strip("-")

    @property
    def leethub_id(self) -> str:
        """Zero-padded frontend id — matches LeetHub v2 (e.g. 0006)."""
        digits = "".join(ch for ch in str(self.problem_id) if ch.isdigit()) or "0"
        return digits.zfill(4)

    @property
    def slug_folder(self) -> str:
        """LeetHub-compatible folder: 0006-zigzag-conversion."""
        return f"{self.leethub_id}-{self.title_slug}"

    @property
    def solution_filename(self) -> str:
        """LeetHub-compatible solution file: 0006-zigzag-conversion.py."""
        return f"{self.slug_folder}.py"

    def to_agent_prompt(self) -> str:
        topics = ", ".join(self.topics) if self.topics else "N/A"
        base = (
            f"Source: {self.source}\n"
            f"Title: {self.problem_id}. {self.title}\n"
            f"Difficulty: {self.difficulty}\n"
            f"Topics: {topics}\n"
            f"URL: {self.url}\n\n"
            f"Description:\n{self.description_text}\n\n"
            f"Starting Code Templates:\n"
        )
        for lang, code in self.templates.items():
            base += f"```{lang}\n{code}\n```\n\n"
        return base

    def crew_inputs(self) -> dict[str, str]:
        return {
            "problem_description": self.to_agent_prompt(),
            "raw_title": self.title,
            "difficulty": self.difficulty,
            "date": self.date,
            "problem_id": self.problem_id,
        }


@dataclass
class ForgeResult:
    """Artifacts produced by the multi-agent brain."""

    problem: Problem
    readme_markdown: str
    solutions: dict[str, str] = field(default_factory=dict)
    local_dir: str | None = None
    github_paths: list[str] = field(default_factory=list)
