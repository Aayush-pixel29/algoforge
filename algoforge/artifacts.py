"""Persist forge artifacts locally before (or instead of) GitHub push."""

from __future__ import annotations

import logging
from pathlib import Path

from algoforge.config import Settings, get_settings
from algoforge.models import ForgeResult

log = logging.getLogger(__name__)


def write_local_artifacts(result: ForgeResult, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    out_root = Path(settings.output_dir).resolve()
    folder = (out_root / result.problem.slug_folder).resolve()

    # Guard against directory traversal from untrusted slug data
    if not str(folder).startswith(str(out_root)):
        raise ValueError(f"Path traversal blocked: {result.problem.slug_folder!r}")

    folder.mkdir(parents=True, exist_ok=True)

    readme_path = folder / "README.md"
    meta_path = folder / "problem.txt"

    for lang, code in result.solutions.items():
        ext = "py" if lang == "python" else "java"
        sol_name = "Solution.java" if ext == "java" else f"{result.problem.slug_folder}.{ext}"
        (folder / sol_name).write_text(
            code if code.endswith("\n") else code + "\n",
            encoding="utf-8",
        )
    readme_path.write_text(
        result.readme_markdown if result.readme_markdown.endswith("\n") else result.readme_markdown + "\n",
        encoding="utf-8",
    )
    meta_path.write_text(result.problem.to_agent_prompt() + "\n", encoding="utf-8")

    result.local_dir = str(folder)
    log.info("Wrote local pack → %s", folder)
    return folder
