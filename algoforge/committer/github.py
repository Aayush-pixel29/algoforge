"""GitHub Committer — push solution + README to the streak repository."""

from __future__ import annotations

import logging

from github import Github, GithubException, InputGitTreeElement
from github.Repository import Repository

import json

from algoforge.config import Settings, get_settings
from algoforge.models import ForgeResult

log = logging.getLogger(__name__)


def _client(settings: Settings) -> Github:
    if not settings.github_token:
        raise ValueError(
            "GITHUB_TOKEN is not set. Add it to .env (see .env.example)."
        )
    return Github(settings.github_token)


def _content_matches(repo: Repository, path: str, content: str, branch: str) -> bool:
    """Check if the remote file already has the same content."""
    try:
        existing = repo.get_contents(path, ref=branch)
        if isinstance(existing, list):
            return False
        return existing.decoded_content.decode("utf-8") == content
    except GithubException:
        return False


def _ensure_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"

def get_curriculum_state(settings: Settings | None = None) -> dict:
    """Read the current curriculum state from the GitHub repo."""
    settings = settings or get_settings()
    if settings.dry_run or not settings.github_token:
        return {"week": 1, "days_in_week": 0, "cf_solved": [], "leetcode_company_solved": [], "last_updated": ""}
    try:
        g = _client(settings)
        repo = g.get_repo(settings.github_repo)
        existing = repo.get_contents("state/curriculum_progress.json", ref=settings.github_branch)
        if isinstance(existing, list):
            return {"week": 1, "days_in_week": 0, "cf_solved": [], "leetcode_company_solved": [], "last_updated": ""}
        return json.loads(existing.decoded_content.decode("utf-8"))
    except GithubException:
        return {"week": 1, "days_in_week": 0, "cf_solved": [], "leetcode_company_solved": [], "last_updated": ""}


def push_forge_result(result: ForgeResult, curriculum_state: dict | None = None, settings: Settings | None = None) -> list[str]:
    """
    Commit solution.py + README.md under dated folder in streak repo.
    Uses a single atomic tree commit instead of per-file commits.
    Does NOT submit to LeetCode (ToS-safe). GitHub streak only.
    """
    settings = settings or get_settings()

    if settings.dry_run:
        log.info("DRY_RUN=true — skipping GitHub push.")
        return []

    log.info("Pushing to %s...", settings.github_repo)
    g = _client(settings)
    repo = g.get_repo(settings.github_repo)
    branch = settings.github_branch

    folder = result.problem.slug_folder
    readme_content = _ensure_newline(result.readme_markdown)
    readme_path = f"{folder}/README.md"
    readme_match = _content_matches(repo, readme_path, readme_content, branch)

    paths = [readme_path]
    tree_elements = []
    
    if not readme_match:
        tree_elements.append(
            InputGitTreeElement(
                path=readme_path,
                mode="100644",
                type="blob",
                content=readme_content,
            )
        )

    for lang, code in result.solutions.items():
        ext = "py" if lang == "python" else "java"
        solution_name = "Solution.java" if ext == "java" else f"{folder}.{ext}"
        solution_path = f"{folder}/{solution_name}"
        solution_content = _ensure_newline(code)
        
        paths.append(solution_path)
        if not _content_matches(repo, solution_path, solution_content, branch):
            tree_elements.append(
                InputGitTreeElement(
                    path=solution_path,
                    mode="100644",
                    type="blob",
                    content=solution_content,
                )
            )

    if curriculum_state:
        state_path = "state/curriculum_progress.json"
        state_content = _ensure_newline(json.dumps(curriculum_state, indent=2))
        paths.append(state_path)
        if not _content_matches(repo, state_path, state_content, branch):
            tree_elements.append(
                InputGitTreeElement(
                    path=state_path,
                    mode="100644",
                    type="blob",
                    content=state_content,
                )
            )

    if not tree_elements:
        log.info("Content unchanged — skipping commit.")
        return paths

    # Atomic commit: create blobs + tree + commit
    commit_msg = (
        f"feat: solve {result.problem.problem_id}. {result.problem.title} "
        f"[{result.problem.difficulty}] — AlgoForge"
    )

    ref = repo.get_git_ref(f"heads/{branch}")
    base_sha = ref.object.sha
    base_commit = repo.get_git_commit(base_sha)
    base_tree = base_commit.tree

    new_tree = repo.create_git_tree(tree_elements, base_tree)
    new_commit = repo.create_git_commit(commit_msg, new_tree, [base_commit])
    ref.edit(new_commit.sha)

    log.info("Atomic commit → https://github.com/%s/tree/%s/%s", settings.github_repo, branch, folder)
    result.github_paths = paths
    return paths
