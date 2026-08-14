"""LeetCode GraphQL ingestion — daily challenge + public profile context."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import logging
import html2text
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from algoforge.config import Settings, get_settings
from algoforge.models import CodeSnippet, Problem

log = logging.getLogger(__name__)

GRAPHQL_URL = "https://leetcode.com/graphql"

DAILY_QUERY = """
query questionOfToday {
  activeDailyCodingChallengeQuestion {
    date
    link
    question {
      questionFrontendId
      title
      titleSlug
      difficulty
      topicTags { name }
      content
      codeSnippets {
        lang
        langSlug
        code
      }
    }
  }
}
"""

PROFILE_QUERY = """
query userPublicProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
      reputation
      starRating
    }
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
  }
}
"""

QUESTION_BY_SLUG = """
query selectProblem($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId
    title
    titleSlug
    difficulty
    topicTags { name }
    content
    codeSnippets {
      lang
      langSlug
      code
    }
  }
}
"""


def _html_to_text(html: str) -> str:
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0
    text = converter.handle(html or "")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _headers(settings: Settings) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com/",
        "User-Agent": (
            "Mozilla/5.0 (compatible; AlgoForge/0.1; +https://github.com/Aayush-pixel29/leetcode)"
        ),
    }
    if settings.leetcode_session:
        headers["Cookie"] = f"LEETCODE_SESSION={settings.leetcode_session}"
    return headers


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _graphql(query: str, variables: dict[str, Any] | None = None, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(
        GRAPHQL_URL,
        json=payload,
        headers=_headers(settings),
        timeout=20,
    )
    response.raise_for_status()
    body = response.json()
    if "errors" in body:
        raise RuntimeError(f"LeetCode GraphQL errors: {body['errors']}")
    return body["data"]


def _question_to_problem(question: dict, *, date_str: str, link: str) -> Problem:
    snippets = [
        CodeSnippet(lang=s["lang"], lang_slug=s["langSlug"], code=s["code"])
        for s in question.get("codeSnippets") or []
    ]
    python = next((s.code for s in snippets if s.lang_slug == "python3"), "")
    slug = question.get("titleSlug") or ""
    url = link if link.startswith("http") else f"https://leetcode.com{link}"
    if not link and slug:
        url = f"https://leetcode.com/problems/{slug}/"

    return Problem(
        source="leetcode",
        problem_id=str(question["questionFrontendId"]),
        title=question["title"],
        difficulty=question["difficulty"],
        date=date_str,
        url=url,
        topics=[t["name"] for t in question.get("topicTags") or []],
        description_html=question.get("content") or "",
        description_text=_html_to_text(question.get("content") or ""),
        python_template=python,
        snippets=snippets,
        extra={"title_slug": slug},
    )


def fetch_daily_challenge(settings: Settings | None = None) -> Problem:
    """Fetch today's LeetCode Daily Coding Challenge."""
    settings = settings or get_settings()
    log.info("Fetching LeetCode daily challenge...")
    data = _graphql(DAILY_QUERY, settings=settings)
    challenge = data["activeDailyCodingChallengeQuestion"]
    if not challenge:
        raise RuntimeError("No active daily coding challenge returned by LeetCode.")

    problem = _question_to_problem(
        challenge["question"],
        date_str=challenge["date"],
        link=challenge.get("link") or "",
    )
    log.info(f"Daily: {problem.problem_id}. {problem.title} [{problem.difficulty}]")
    return problem


def fetch_profile(username: str | None = None, settings: Settings | None = None) -> dict[str, Any] | None:
    """Fetch public profile stats for learning-path context (no submission automation)."""
    settings = settings or get_settings()
    username = username or settings.leetcode_username
    log.info(f"Loading public profile @{username}...")
    try:
        data = _graphql(PROFILE_QUERY, {"username": username}, settings=settings)
        user = data.get("matchedUser")
        if not user:
            log.info(f"Profile @{username} not found (public GraphQL).")
            return None
        log.info(f"Profile loaded for @{user['username']}")
        return user
    except Exception as exc:  # noqa: BLE001 — profile is optional context
        log.debug("Profile fetch skipped: %s", exc, exc_info=True)
        return None


def fetch_problem_by_slug(title_slug: str, settings: Settings | None = None) -> Problem:
    """Fetch any problem by slug (useful for backfills / practice picks)."""
    settings = settings or get_settings()
    data = _graphql(QUESTION_BY_SLUG, {"titleSlug": title_slug}, settings=settings)
    question = data.get("question")
    if not question:
        raise RuntimeError(f"Problem not found: {title_slug}")
    return _question_to_problem(
        question,
        date_str=date.today().isoformat(),
        link=f"/problems/{title_slug}/",
    )


def fetch_for_pipeline(settings: Settings | None = None) -> tuple[Problem, dict[str, Any] | None]:
    """Primary entry: daily challenge + optional profile context."""
    settings = settings or get_settings()
    profile = fetch_profile(settings=settings)
    problem = fetch_daily_challenge(settings=settings)
    if profile:
        problem.extra["solver_profile"] = {
            "username": profile.get("username"),
            "ranking": (profile.get("profile") or {}).get("ranking"),
            "ac_stats": profile.get("submitStatsGlobal"),
        }
    return problem, profile
