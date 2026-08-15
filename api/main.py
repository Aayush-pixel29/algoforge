"""AlgoForge web API — thin FastAPI control plane over the engine."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from algoforge.artifacts import write_local_artifacts
from algoforge.brain import run_brain
from algoforge.committer import push_forge_result
from algoforge.config import Settings, get_settings, setup_logging
from algoforge.ingestion import fetch_for_pipeline, fetch_problem_by_slug

setup_logging()
log = logging.getLogger(__name__)

app = FastAPI(title="AlgoForge", version="0.3.0")

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,https://algoforge-dashboard-9i6.pages.dev"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple API key auth for mutation endpoints
API_KEY = os.getenv("ALGOFORGE_API_KEY", "")


def require_auth(x_api_key: str = Header(default="")):
    """Guard mutation endpoints with an optional API key."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(403, "Invalid or missing API key")


# job_id -> {status, events[], result?, task?}
JOBS: dict[str, dict[str, Any]] = {}


class ForgeRequest(BaseModel):
    slug: str | None = None
    dry_run: bool = True


class SettingsUpdate(BaseModel):
    leetcode_username: str | None = None
    github_repo: str | None = None
    github_branch: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    ollama_base_url: str | None = None
    dry_run: bool | None = None


def _problem_dict(p) -> dict:
    return {
        "source": p.source,
        "problem_id": p.problem_id,
        "title": p.title,
        "difficulty": p.difficulty,
        "date": p.date,
        "url": p.url,
        "topics": p.topics,
        "description_text": p.description_text,
        "python_template": p.templates.get("python", ""),
        "slug_folder": p.slug_folder,
        "title_slug": p.title_slug,
    }


def _emit(job_id: str, stage: str, message: str, **extra: Any) -> None:
    ev = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "message": message,
        **extra,
    }
    JOBS[job_id]["events"].append(ev)


def _safe_artifact_path(output_dir: Path, folder: str) -> Path:
    """Resolve artifact path and guard against directory traversal."""
    root = output_dir.resolve()
    target = (root / folder).resolve()
    if not str(target).startswith(str(root)):
        raise HTTPException(403, "Path traversal blocked")
    return target


def sanitize_slug(raw: str | None) -> str | None:
    """Normalize user input (title or URL) into a valid LeetCode slug."""
    if not raw:
        return None
    m = re.search(r"problems/([^/]+)", raw)
    if m:
        return m.group(1)
    cleaned = raw.strip().lower()
    cleaned = re.sub(r"[^a-z0-9\s-]", "", cleaned)
    cleaned = re.sub(r"[\s_]+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    return cleaned.strip("-")


@app.get("/api/health")
async def health():
    s = get_settings()
    ollama_ok = False
    models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{s.ollama_base_url.rstrip('/')}/api/tags")
            if r.status_code == 200:
                ollama_ok = True
                models = [m.get("name", "") for m in r.json().get("models", [])]
    except Exception:
        pass
    return {
        "ok": True,
        "ollama": ollama_ok,
        "models": models,
        "github_token": bool(s.github_token),
        "github_repo": s.github_repo,
        "leetcode_username": s.leetcode_username,
        "llm": f"{s.llm_provider}/{s.llm_model}",
        "dry_run": s.dry_run,
    }

class SettingsUpdate(BaseModel):
    leetcode_username: str | None = None
    github_repo: str | None = None
    github_branch: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    ollama_base_url: str | None = None
    dry_run: bool | None = None
    interview_date: str | None = None


@app.get("/api/scout")
async def scout(slug: str | None = None, random: bool = False):
    s = get_settings()
    slug = sanitize_slug(slug)
    try:
        if random:
            from algoforge.ingestion.company_bank import fetch_company_list
            import random as rand
            companies = s.target_companies or ["Google", "Meta", "Amazon"]
            target_company = rand.choice(companies)
            problems = await asyncio.to_thread(fetch_company_list, target_company)
            slugs = []
            for p in problems:
                url = p.get("url", "")
                if url and "leetcode.com/problems/" in url:
                    extracted = url.split("leetcode.com/problems/")[1].strip("/")
                    slugs.append(extracted)
            if slugs:
                slug = rand.choice(slugs)

        if slug:
            problem = await asyncio.to_thread(fetch_problem_by_slug, slug, s)
            profile = None
        else:
            problem, profile = await asyncio.to_thread(fetch_for_pipeline, s)
    except Exception as e:
        raise HTTPException(502, str(e)) from e
    return {
        "problem": _problem_dict(problem),
        "profile": {
            "username": (profile or {}).get("username"),
            "ranking": ((profile or {}).get("profile") or {}).get("ranking"),
        }
        if profile
        else None,
    }


from algoforge.ingestion.codeforces import fetch_problem as fetch_cf
from crewai import Agent, Task, Crew
from algoforge.brain.llm import build_llm

@app.get("/api/phase2/codeforces")
async def scout_codeforces(contest_id: int, index: str):
    """Phase 2: Scout a Codeforces problem via public API."""
    try:
        problem = await asyncio.to_thread(fetch_cf, contest_id, index.upper())
        return {"problem": _problem_dict(problem)}
    except Exception as e:
        raise HTTPException(502, str(e)) from e

class ResearchRequest(BaseModel):
    problem_id: str
    title: str

@app.post("/api/phase2/research")
async def run_research_agent(req: ResearchRequest):
    """Phase 2: Deploy a Research Sub-Agent to analyze the problem constraints."""
    s = get_settings()
    try:
        llm = build_llm(s)
        researcher = Agent(
            role="Algorithm Constraint Researcher",
            goal="Analyze the problem title/ID and outline potential edge cases or constraints to watch out for.",
            backstory="You are a meticulous competitive programmer who always analyzes constraints before writing any code.",
            llm=llm,
            verbose=False
        )
        task = Task(
            description=f"Analyze Codeforces problem {req.problem_id}: {req.title}. List 3 potential edge cases or constraints.",
            expected_output="A bulleted list of 3 edge cases.",
            agent=researcher
        )
        crew = Crew(agents=[researcher], tasks=[task], verbose=False)
        result = await asyncio.to_thread(crew.kickoff)
        out = getattr(result, "raw", str(result))
        return {"response": f"[Agent Output]:\n{out}"}
    except Exception as e:
        log.exception("Research agent failed")
        raise HTTPException(500, f"Agent failed: {e}")

import time

@app.post("/api/forge")
async def start_forge(body: ForgeRequest, _auth=Depends(require_auth)):
    # Sweep old jobs
    now = time.time()
    to_delete = []
    for jid, jdata in JOBS.items():
        if jdata["status"] in ("done", "error"):
            if now - jdata.get("created_at", now) > 7200:  # 2 hours
                to_delete.append(jid)
    for jid in to_delete:
        del JOBS[jid]

    job_id = uuid.uuid4().hex[:12]
    clean_slug = sanitize_slug(body.slug)
    JOBS[job_id] = {"status": "queued", "events": [], "result": None, "error": None, "created_at": time.time()}
    task = asyncio.create_task(_run_job(job_id, clean_slug, body.dry_run))
    JOBS[job_id]["task"] = task  # prevent GC of the task
    log.info("Forge job %s queued (slug=%s, dry_run=%s)", job_id, clean_slug, body.dry_run)
    return {"job_id": job_id}


async def _run_job(job_id: str, slug: str | None, dry_run: bool) -> None:
    s = get_settings().model_copy(update={"dry_run": dry_run})
    JOBS[job_id]["status"] = "running"
    try:
        _emit(job_id, "scout", "Fetching problem...")
        if slug:
            problem = await asyncio.to_thread(fetch_problem_by_slug, slug, s)
        else:
            problem, _ = await asyncio.to_thread(fetch_for_pipeline, s)
        _emit(job_id, "scout", f"Got {problem.problem_id}. {problem.title}", problem=_problem_dict(problem))

        _emit(job_id, "brain", "Master Agent solving + writing teaching notes...")
        result = await asyncio.to_thread(run_brain, problem, s)
        _emit(job_id, "brain", "Agents finished")

        _emit(job_id, "artifacts", "Writing local pack...")
        folder = await asyncio.to_thread(write_local_artifacts, result, s)
        _emit(job_id, "artifacts", f"Wrote {folder}")

        if dry_run:
            _emit(job_id, "commit", "Dry-run — skipped GitHub push")
            paths: list[str] = []
        else:
            _emit(job_id, "commit", "Pushing to GitHub...")
            paths = await asyncio.to_thread(push_forge_result, result, s)
            _emit(job_id, "commit", f"Pushed: {', '.join(paths) or 'ok'}")

        JOBS[job_id]["result"] = {
            "folder": result.problem.slug_folder,
            "local_dir": result.local_dir,
            "github_paths": paths,
            "solutions": result.solutions,
            "readme_markdown": result.readme_markdown,
            "problem": _problem_dict(result.problem),
        }
        JOBS[job_id]["status"] = "done"
        _emit(job_id, "done", "Pipeline complete")
    except Exception as e:
        log.exception("Forge job %s failed", job_id)
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)
        _emit(job_id, "error", str(e))


@app.get("/api/forge/{job_id}")
async def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return {
        "job_id": job_id,
        "status": job["status"],
        "error": job["error"],
        "result": job["result"],
        "events": job["events"],
    }


@app.get("/api/forge/{job_id}/events")
async def forge_events(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "job not found")

    async def gen():
        idx = 0
        while True:
            job = JOBS[job_id]
            while idx < len(job["events"]):
                yield f"data: {json.dumps(job['events'][idx])}\n\n"
                idx += 1
            if job["status"] in ("done", "error"):
                yield f"data: {json.dumps({'stage': 'end', 'message': job['status']})}\n\n"
                break
            await asyncio.sleep(0.4)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/artifacts")
async def list_artifacts():
    root = Path(get_settings().output_dir).resolve()
    if not root.exists():
        return {"items": []}
    items = []
    for d in sorted(root.iterdir(), reverse=True):
        if d.is_dir():
            items.append(
                {
                    "folder": d.name,
                    "has_readme": (d / "README.md").exists(),
                    "solution": next((p.name for p in d.glob("*.py")), None),
                }
            )
    return {"items": items}


@app.get("/api/artifacts/{folder}")
async def get_artifact(folder: str):
    root = _safe_artifact_path(Path(get_settings().output_dir), folder)
    if not root.is_dir():
        raise HTTPException(404, "not found")
    readme = root / "README.md"
    problem = root / "problem.txt"
    
    solutions = {}
    for ext, lang in [("py", "python"), ("java", "java")]:
        f = next(root.glob(f"*.{ext}"), None)
        if f:
            solutions[lang] = {"name": f.name, "code": f.read_text(encoding="utf-8")}
            
    return {
        "folder": folder,
        "readme_markdown": readme.read_text(encoding="utf-8") if readme.exists() else "",
        "solutions": solutions,
        "problem_text": problem.read_text(encoding="utf-8") if problem.exists() else "",
    }


@app.get("/api/settings")
async def get_cfg():
    s = get_settings()
    return {
        "leetcode_username": s.leetcode_username,
        "github_repo": s.github_repo,
        "github_branch": s.github_branch,
        "llm_provider": s.llm_provider,
        "llm_model": s.llm_model,
        "ollama_base_url": s.ollama_base_url,
        "dry_run": s.dry_run,
        "github_token_set": bool(s.github_token),
        "interview_date": getattr(s, "interview_date", None) or os.environ.get("INTERVIEW_DATE", ""),
    }


@app.put("/api/settings")
async def put_cfg(body: SettingsUpdate, _auth=Depends(require_auth)):
    """Update non-secret settings in process + patch .env keys (no token write via UI)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    mapping = {
        "leetcode_username": "LEETCODE_USERNAME",
        "github_repo": "GITHUB_REPO",
        "github_branch": "GITHUB_BRANCH",
        "llm_provider": "LLM_PROVIDER",
        "llm_model": "LLM_MODEL",
        "ollama_base_url": "OLLAMA_BASE_URL",
        "dry_run": "DRY_RUN",
        "interview_date": "INTERVIEW_DATE",
    }
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates and env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
        keys_done = set()
        out = []
        for line in lines:
            wrote = False
            for field, env_key in mapping.items():
                if field in updates and line.startswith(f"{env_key}="):
                    val = updates[field]
                    out.append(f"{env_key}={str(val).lower() if isinstance(val, bool) else val}")
                    keys_done.add(field)
                    wrote = True
                    break
            if not wrote:
                out.append(line)
        for field, env_key in mapping.items():
            if field in updates and field not in keys_done:
                val = updates[field]
                out.append(f"{env_key}={str(val).lower() if isinstance(val, bool) else val}")
        env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    get_settings.cache_clear()
    return await get_cfg()

from functools import lru_cache
import time
from datetime import datetime, timedelta, timezone

@lru_cache(maxsize=1)
def _fetch_streak_cached(ttl_hash: int):
    s = get_settings()
    if not s.github_token or not s.github_repo:
        return {"current_streak": 0, "longest_streak": 0, "calendar": []}
    
    try:
        from algoforge.committer.github import _client
        g = _client(s)
        repo = g.get_repo(s.github_repo)
        since = datetime.now(timezone.utc) - timedelta(days=90)
        commits = repo.get_commits(since=since, author=g.get_user().login)
        
        # Build set of days with commits
        commit_days = set()
        for c in commits:
            commit_days.add(c.commit.author.date.strftime("%Y-%m-%d"))
            
        calendar = []
        curr_date = since
        end_date = datetime.now(timezone.utc)
        current_streak = 0
        longest_streak = 0
        current_streak_active = True
        
        # Traverse backwards from today to find current streak
        for i in range(90):
            d_str = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            if d_str in commit_days:
                if current_streak_active:
                    current_streak += 1
            else:
                if i > 0: # missed a day (ignore today if not committed yet)
                    current_streak_active = False
                    
        # Calculate longest streak
        temp_streak = 0
        for i in range(90, -1, -1):
            d_str = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            active = d_str in commit_days
            calendar.append({"date": d_str, "active": active})
            if active:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
                
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "calendar": calendar
        }
    except Exception as e:
        log.error(f"Failed to fetch streak: {e}")
        return {"current_streak": 0, "longest_streak": 0, "calendar": []}

@app.get("/api/streak")
async def get_streak():
    """Returns 90-day GitHub commit streak for the user."""
    # cache TTL of 1 hour (3600 seconds)
    return await asyncio.to_thread(_fetch_streak_cached, int(time.time() / 3600))
