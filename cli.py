"""CLI entrypoint for AlgoForge."""

from __future__ import annotations

import argparse
import logging
import sys
import traceback


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="algoforge",
        description=(
            "Fetch a coding challenge, solve + teach via multi-agent AI, "
            "and commit to your GitHub streak repo."
        ),
    )
    parser.add_argument(
        "--slug",
        help="LeetCode title slug (e.g. two-sum). Default: today's daily challenge.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write local artifacts only; do not push to GitHub.",
    )
    parser.add_argument(
        "--scout-only",
        action="store_true",
        help="Only fetch and print the problem (no LLM / no commit).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG-level logging with full tracebacks.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    from algoforge.config import setup_logging
    setup_logging(verbose=args.verbose)
    log = logging.getLogger(__name__)

    if args.scout_only:
        from algoforge.config import get_settings
        from algoforge.ingestion import fetch_for_pipeline, fetch_problem_by_slug

        settings = get_settings()
        if args.slug:
            problem = fetch_problem_by_slug(args.slug, settings=settings)
        else:
            problem, profile = fetch_for_pipeline(settings=settings)
            if profile:
                log.info("Profile: @%s", profile.get('username'))
        print(problem.to_agent_prompt()[:1200])
        print("...")
        return 0

    from algoforge.pipeline import run_pipeline

    try:
        run_pipeline(slug=args.slug, dry_run=args.dry_run or None)
    except Exception as exc:  # noqa: BLE001 — CLI surface
        log.error("Pipeline failed: %s", exc)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
