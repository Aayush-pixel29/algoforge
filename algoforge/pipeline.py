"""End-to-end pipeline: Scout → Brain → Artifacts → Committer."""

from __future__ import annotations

import logging

from algoforge.artifacts import write_local_artifacts
from algoforge.brain import run_brain
from algoforge.committer import push_forge_result
from algoforge.config import Settings, get_settings
from algoforge.ingestion import fetch_for_pipeline, fetch_problem_by_slug
from algoforge.models import ForgeResult

log = logging.getLogger(__name__)


def run_pipeline(
    *,
    slug: str | None = None,
    dry_run: bool | None = None,
    settings: Settings | None = None,
) -> ForgeResult:
    """
    Execute one AlgoForge cycle.

    - Default: LeetCode Daily Challenge (learner profile from LEETCODE_USERNAME)
    - Optional slug: forge a specific problem (backfill / practice)
    """
    settings = settings or get_settings()
    if dry_run is not None:
        settings = settings.model_copy(update={"dry_run": dry_run})

    log.info("=" * 60)
    log.info("  AlgoForge — Scout → Brain → Commit")
    log.info("  Learner : @%s", settings.leetcode_username)
    log.info("  Target  : %s", settings.github_repo)
    log.info("  LLM     : %s/%s", settings.llm_provider, settings.llm_model)
    log.info("  Dry-run : %s", settings.dry_run)
    log.info("=" * 60)

    if slug:
        log.info("Fetching problem by slug: %s", slug)
        problem = fetch_problem_by_slug(slug, settings=settings)
    else:
        problem, _profile = fetch_for_pipeline(settings=settings)

    result = run_brain(problem, settings=settings)
    write_local_artifacts(result, settings=settings)
    push_forge_result(result, settings=settings)

    log.info("=" * 60)
    log.info("  Pipeline complete.")
    if result.local_dir:
        log.info("  Local  : %s", result.local_dir)
    if result.github_paths:
        log.info("  GitHub : %s", ', '.join(result.github_paths))
    log.info("=" * 60)
    return result
