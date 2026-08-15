"""Loads and caches the community-maintained company-wise problem CSVs."""

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

RAW_BASE = "https://raw.githubusercontent.com/liquidslr/leetcode-company-wise-problems/main/companies"
CACHE_DIR = Path(".cache/company")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_company_list(company: str, window: str = "3. Three Months") -> list[dict]:
    """
    Downloads the company-wise CSV, caches to .cache/company/{company}_{window}.csv (24h TTL).
    Returns list of {difficulty, title, url, topics, frequency}.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # We use JSON caching for simplicity of storing parsed data
    safe_company = company.replace(" ", "_")
    safe_window = window.replace(" ", "_")
    cache_file = CACHE_DIR / f"{safe_company}_{safe_window}.json"
    
    # Check cache TTL (24h)
    if cache_file.exists():
        now = datetime.now(timezone.utc).timestamp()
        if now - cache_file.stat().st_mtime < 86400:
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

    url = f"{RAW_BASE}/{company}/{window}.csv".replace(" ", "%20")
    log.info(f"Fetching company bank for {company} from {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
        
        reader = csv.DictReader(content.splitlines())
        problems = []
        for row in reader:
            problems.append({
                "difficulty": row.get("Difficulty", ""),
                "title": row.get("Title", ""),
                "url": row.get("Leetcode Question Link", ""),
                "topics": row.get("Topics", ""),
                "frequency": row.get("Frequency", "0"),
                "acceptance_rate": row.get("Acceptance", "")
            })
            
        # Cache the parsed list
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(problems, f)
            
        return problems
    except Exception as e:
        log.error(f"Failed to fetch company list for {company}: {e}")
        return []
