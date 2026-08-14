"""Codeforces scout — public REST API (phase 2 hook)."""

from __future__ import annotations

import logging
from datetime import date

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from algoforge.models import Problem

log = logging.getLogger(__name__)

API = "https://codeforces.com/api"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def fetch_problem(contest_id: int, index: str) -> Problem:
    """
    Fetch a Codeforces problem statement via the public API problemset.

    Note: CF statements are often lighter via API; full HTML may need the problem page.
    This is a scaffold for multi-platform support.
    """
    resp = requests.get(f"{API}/problemset.problems", timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "OK":
        raise RuntimeError(f"Codeforces API error: {payload}")

    problems = payload["result"]["problems"]
    match = next(
        (p for p in problems if p.get("contestId") == contest_id and p.get("index") == index),
        None,
    )
    if not match:
        raise RuntimeError(f"Codeforces problem {contest_id}{index} not found.")

    title = match.get("name", f"{contest_id}{index}")
    rating = match.get("rating")
    tags = match.get("tags") or []
    return Problem(
        source="codeforces",
        problem_id=f"{contest_id}{index}",
        title=title,
        difficulty=str(rating) if rating else "unknown",
        date=date.today().isoformat(),
        url=f"https://codeforces.com/problemset/problem/{contest_id}/{index}",
        topics=list(tags),
        description_text=(
            f"Codeforces {contest_id}{index}: {title}\n"
            f"Tags: {', '.join(tags)}\n"
            f"Open the URL for the full statement: "
            f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
        ),
        templates={
            "python": (
                "def solve():\n"
                "    # TODO: implement\n"
                "    pass\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            )
        },
        extra={"contest_id": contest_id, "index": index},
    )
