"""End-to-end pipeline: Scout → Brain → Artifacts → Committer."""

from __future__ import annotations

import logging

from algoforge.artifacts import write_local_artifacts
from algoforge.brain import run_brain
from algoforge.committer import push_forge_result
from algoforge.committer.github import get_curriculum_state
from algoforge.config import Settings, get_settings
from algoforge.ingestion import fetch_for_pipeline, fetch_problem_by_slug
from algoforge.ingestion.codeforces import fetch_problem as fetch_cf
from algoforge.scheduler import pick_todays_target
from algoforge.models import ForgeResult
from algoforge.notifications import send_daily_reminder

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
        state = None
    else:
        state = get_curriculum_state(settings=settings)
        pick = pick_todays_target(settings, state)
        if pick.source == "leetcode":
            problem, _profile = fetch_for_pipeline(settings=settings)
        elif pick.source == "codeforces":
            problem = fetch_cf(pick.slug_or_ids["contest_id"], pick.slug_or_ids["index"])
            if state:
                state["cf_solved"].append(problem.problem_id)
        else:  # company
            problem = fetch_problem_by_slug(pick.slug_or_ids["slug"], settings=settings)
            if state:
                state["leetcode_company_solved"].append(problem.problem_id)
                
        # Advance curriculum if day threshold met
        if state:
            state["days_in_week"] += 1
            if state["days_in_week"] >= 5:
                state["week"] += 1
                state["days_in_week"] = 0
            import datetime
            state["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d")

    result = run_brain(problem, settings=settings)
    write_local_artifacts(result, settings=settings)
    push_forge_result(result, curriculum_state=state, settings=settings)

    log.info("=" * 60)
    log.info("  Pipeline complete.")
    if result.local_dir:
        log.info("  Local  : %s", result.local_dir)
    if result.github_paths:
        log.info("  GitHub : %s", ', '.join(result.github_paths))
    log.info("=" * 60)
    
    send_daily_reminder(result, settings=settings)
    return result
