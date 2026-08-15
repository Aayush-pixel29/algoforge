"""Decides *what* to forge today: which platform, which problem."""

import os
import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from urllib.request import urlopen, Request

from algoforge.config import Settings
from algoforge.curriculum import CURRICULUM
from algoforge.ingestion.company_bank import fetch_company_list

log = logging.getLogger(__name__)

@dataclass
class PickResult:
    source: str
    slug_or_ids: dict

def pick_codeforces_problem(tag: str, rating_min: int, rating_max: int, exclude: set[str]) -> tuple[int, str]:
    """
    GET https://codeforces.com/api/problemset.problems
    Filter by tag, rating band, and exclusion set.
    Returns (contest_id, index).
    """
    url = "https://codeforces.com/api/problemset.problems"
    log.info("Fetching Codeforces problemset...")
    try:
        req = Request(url)
        with urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        if data.get("status") != "OK":
            raise ValueError("Codeforces API returned non-OK status.")
            
        problems = data["result"]["problems"]
        
        candidates = []
        for p in problems:
            # Codeforces rating can be absent for some problems
            if "rating" not in p:
                continue
            
            c_id = p.get("contestId")
            idx = p.get("index")
            if not c_id or not idx:
                continue
                
            prob_id = f"{c_id}{idx}"
            if prob_id in exclude:
                continue
                
            if rating_min <= p["rating"] <= rating_max:
                if tag in p.get("tags", []):
                    candidates.append(p)
                    
        if not candidates:
            raise ValueError(f"No Codeforces problem found for tag '{tag}' in range {rating_min}-{rating_max}.")
            
        # Sort by rating ascending (easiest in band)
        candidates.sort(key=lambda x: x["rating"])
        best = candidates[0]
        return best["contestId"], best["index"]
        
    except Exception as e:
        log.error(f"Failed to pick Codeforces problem: {e}")
        raise ValueError(f"Failed to pick Codeforces problem: {e}")

def pick_todays_target(settings: Settings, curriculum_state: dict) -> PickResult:
    """
    Rotation based on PLATFORM_ROTATION env (or day of week).
    """
    rotation_env = os.environ.get(
        "PLATFORM_ROTATION",
        "leetcode,leetcode,codeforces,leetcode,company,leetcode,codeforces"
    )
    rotation = [r.strip() for r in rotation_env.split(",")]
    today = datetime.now(timezone.utc).weekday()  # Mon=0, Sun=6
    source = rotation[today % len(rotation)]
    
    if source == "codeforces":
        # Resolve curriculum state
        week = curriculum_state.get("week", 1)
        # 1-indexed week, curriculum is 0-indexed. Wait, curriculum tuples are string ranges "1-2"
        
        # Find matching curriculum config
        curr_config = CURRICULUM[-1] # fallback to last
        for item in CURRICULUM:
            week_str = item[0]
            if "-" in week_str:
                w_start, w_end = map(int, week_str.split("-"))
                if w_start <= week <= w_end:
                    curr_config = item
                    break
            else:
                if week == int(week_str):
                    curr_config = item
                    break
                    
        cf_tag = curr_config[2] # e.g. "implementation,strings"
        # Pick one tag randomly or just the first if comma separated
        primary_cf_tag = cf_tag.split(",")[0].strip()
        r_min, r_max = curr_config[3]
        
        exclude = set(curriculum_state.get("cf_solved", []))
        try:
            contest_id, index = pick_codeforces_problem(primary_cf_tag, r_min, r_max, exclude)
            return PickResult(source="codeforces", slug_or_ids={"contest_id": contest_id, "index": index})
        except ValueError:
            log.warning("Codeforces pick failed, falling back to leetcode.")
            source = "leetcode"
            
    if source == "company":
        # round-robin based on week and days
        companies = settings.target_companies
        if companies:
            day_offset = curriculum_state.get("week", 1) * 7 + curriculum_state.get("days_in_week", 0)
            target_company = companies[day_offset % len(companies)]
            
            problems = fetch_company_list(target_company)
            if problems:
                exclude = set(curriculum_state.get("leetcode_company_solved", []))
                # Pick highest frequency unsolved problem
                # CSV frequency usually out of 100 or something, but we sort by frequency desc
                
                # Filter out solved (title slug extraction from URL)
                candidates = []
                for p in problems:
                    url = p["url"]
                    if not url or "leetcode.com/problems/" not in url:
                        continue
                    slug = url.split("leetcode.com/problems/")[1].strip("/")
                    if slug not in exclude:
                        # parse float frequency
                        freq = 0.0
                        try:
                            freq = float(p.get("frequency", 0))
                        except ValueError:
                            pass
                        candidates.append((freq, slug, p))
                
                if candidates:
                    candidates.sort(key=lambda x: x[0], reverse=True)
                    best_slug = candidates[0][1]
                    return PickResult(source="company", slug_or_ids={"slug": best_slug})
                    
        log.warning("Company pick failed, falling back to leetcode.")
        source = "leetcode"
        
    # Default: leetcode daily challenge
    return PickResult(source="leetcode", slug_or_ids={})
