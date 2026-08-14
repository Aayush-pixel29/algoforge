# AlgoForge

Autonomous multi-agent pipeline that fetches a coding challenge, **solves it**, **teaches you** (logic + 5 real-world project examples), and **commits** to [`Aayush-pixel29/leetcode`](https://github.com/Aayush-pixel29/leetcode) so your GitHub streak stays green.

Learner profile: [leetcode.com/u/pYwmntvkNk](https://leetcode.com/u/pYwmntvkNk/)

> **Design choice (important):** AlgoForge does **not** auto-submit to LeetCode. LeetCode submission automation fights Cloudflare and violates ToS. We forge learning materials + GitHub commits; you paste into LeetCode manually if you want the platform streak.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AlgoForge Pipeline                          │
│                                                                 │
│  ┌──────────────┐   ┌──────────────────────────┐   ┌─────────┐ │
│  │ 1. Scout     │──▶│ 2. Brain (CrewAI)        │──▶│ 3. VCS  │ │
│  │              │   │                          │   │         │ │
│  │ LeetCode GQL │   │ Master Agent (1-pass)    │   │ PyGithub│ │
│  │ + profile    │   │ optimized code + README  │   │ streak  │ │
│  │ Codeforces*  │   │ + 5 production examples  │   │ repo    │ │
│  └──────────────┘   └──────────────────────────┘   └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
   problem.txt              solution.py              GitHub commit
   (local meta)             README.md                dated folder
```

| Module | Persona | Job |
|--------|---------|-----|
| `ingestion/` | **Scout** | Daily challenge via GraphQL; optional public profile `@pYwmntvkNk` |
| `brain/` | **Master Agent** | Optimal code → teaching README with 5 real-world examples → polish |
| `committer/` | **Committer** | Upsert `solution.py` + `README.md` into `Aayush-pixel29/leetcode` |
| `artifacts.py` | — | Always write a local pack under `output/` |

\* Codeforces scout is scaffolded (`ingestion/codeforces.py`) for phase 2.

---

## Repo layout

```
AlgoForge/
├── main.py                      # python main.py
├── algoforge/
│   ├── cli.py                   # CLI
│   ├── config.py                # typed settings from .env
│   ├── models.py                # Problem / ForgeResult
│   ├── pipeline.py              # orchestrator
│   ├── artifacts.py             # local output writer
│   ├── ingestion/
│   │   ├── leetcode.py          # GraphQL scout + profile
│   │   └── codeforces.py        # REST scaffold
│   ├── brain/
│   │   ├── llm.py               # Ollama | OpenAI | Anthropic
│   │   ├── prompts.py
│   │   └── agents.py            # CrewAI crew
│   └── committer/
│       └── github.py
├── .github/workflows/daily_forge.yml
├── requirements.txt
├── .env.example
└── output/                      # local forge packs (gitignored)
```

Remote streak repo ([Aayush-pixel29/leetcode](https://github.com/Aayush-pixel29/leetcode)) uses **LeetHub v2** naming:

```
0006-zigzag-conversion/
├── 0006-zigzag-conversion.java   # existing LeetHub solutions
└── README.md

3348-smallest-divisible-digit-product-ii/   # AlgoForge daily packs
├── 3348-smallest-divisible-digit-product-ii.py
└── README.md   # intuition, walkthrough, complexity, 5 real-world examples
```

---

## Website (laptop)

```powershell
# terminal 1 — API
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# terminal 2 — UI
cd web
npm install
npm run dev
```

Open http://localhost:5173 — Dashboard → Forge → Study.

Keep Docker Ollama running: `docker compose up -d`



```powershell
cd D:\AlgoForge\AlgoForge
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
copy .env.example .env
```

Edit `.env`:

```env
GITHUB_TOKEN=ghp_...
GITHUB_REPO=Aayush-pixel29/leetcode
LEETCODE_USERNAME=pYwmntvkNk
LLM_PROVIDER=ollama
LLM_MODEL=llama3
```

### Local LLM (Ollama)

```powershell
ollama pull llama3
ollama serve
```

### Scout only (no LLM cost)

```powershell
python main.py --scout-only
```

### Full dry-run (solve + teach, no GitHub push)

```powershell
python main.py --dry-run
```

### Full streak run

```powershell
python main.py
```

### Specific problem backfill

```powershell
python main.py --slug two-sum --dry-run
```

---

## GitHub Actions (cloud cron)

Workflow: `.github/workflows/daily_forge.yml` (08:00 IST).

Repo secrets / vars on **this** AlgoForge repo:

| Name | Type | Purpose |
|------|------|---------|
| `STREAK_GITHUB_TOKEN` | secret | PAT with `repo` on `Aayush-pixel29/leetcode` |
| `OPENAI_API_KEY` | secret | if `LLM_PROVIDER=openai` |
| `LEETCODE_USERNAME` | variable | default `pYwmntvkNk` |
| `GITHUB_REPO` | variable | default `Aayush-pixel29/leetcode` |

Actions runners don't have Ollama — use OpenAI/Anthropic in CI.

---

## Safety rails

1. **No LeetCode submission bots** — streak target is GitHub only.
2. **Secrets stay in `.env` / Actions secrets** — never hardcoded.
3. **`DRY_RUN=true`** — forge locally while iterating on prompts.
4. **Idempotent commits** — re-runs update the same dated folder.

---

## Roadmap

- [x] LeetCode daily GraphQL scout
- [x] Profile-aware config (`pYwmntvkNk`)
- [x] Optimized single-pass Master Agent crew
- [x] GitHub streak committer
- [x] GitHub Actions schedule
- [ ] Codeforces full statement + contest mode
- [ ] Difficulty-aware problem picker from unsolved set
- [ ] Local test harness against sample I/O
