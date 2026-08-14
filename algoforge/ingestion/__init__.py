"""Ingestion package — problem scouts for each platform."""

from algoforge.ingestion.leetcode import (
    fetch_daily_challenge,
    fetch_for_pipeline,
    fetch_problem_by_slug,
    fetch_profile,
)

__all__ = [
    "fetch_daily_challenge",
    "fetch_for_pipeline",
    "fetch_problem_by_slug",
    "fetch_profile",
]
