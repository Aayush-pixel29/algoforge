const BASE = import.meta.env.VITE_API_URL || "";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || r.statusText);
  }
  return r.json() as Promise<T>;
}

export type Health = {
  ok: boolean;
  ollama: boolean;
  models: string[];
  github_token: boolean;
  github_repo: string;
  leetcode_username: string;
  llm: string;
  dry_run: boolean;
};

export type Problem = {
  problem_id: string;
  title: string;
  difficulty: string;
  date: string;
  url: string;
  topics: string[];
  description_text: string;
  slug_folder: string;
  title_slug: string;
  acceptance_rate?: string;
};

export type StreakData = {
  current_streak: number;
  longest_streak: number;
  calendar: { date: string; active: boolean }[];
};

export type AppSettings = {
  leetcode_username: string;
  github_repo: string;
  github_branch: string;
  llm_provider: string;
  llm_model: string;
  ollama_base_url: string;
  dry_run: boolean;
  github_token_set: boolean;
  interview_date: string;
};
