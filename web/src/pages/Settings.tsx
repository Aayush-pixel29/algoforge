import { useEffect, useState } from "react";
import { api } from "../api";

type Cfg = {
  leetcode_username: string;
  github_repo: string;
  github_branch: string;
  llm_provider: string;
  llm_model: string;
  ollama_base_url: string;
  dry_run: boolean;
  github_token_set: boolean;
};

export default function Settings() {
  const [cfg, setCfg] = useState<Cfg | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    api<Cfg>("/api/settings", { signal: controller.signal })
      .then(setCfg)
      .catch((e) => {
        if (!controller.signal.aborted) setErr(String(e));
      });
    return () => controller.abort();
  }, []);

  async function save() {
    if (!cfg) return;
    setSaving(true);
    setMsg("");
    setErr("");
    try {
      const next = await api<Cfg>("/api/settings", {
        method: "PUT",
        body: JSON.stringify({
          leetcode_username: cfg.leetcode_username,
          github_repo: cfg.github_repo,
          github_branch: cfg.github_branch,
          llm_provider: cfg.llm_provider,
          llm_model: cfg.llm_model,
          ollama_base_url: cfg.ollama_base_url,
          dry_run: cfg.dry_run,
        }),
      });
      setCfg(next);
      setMsg("✓ Saved to .env");
      setTimeout(() => setMsg(""), 3000);
    } catch (e) {
      setErr(String(e));
    } finally {
      setSaving(false);
    }
  }

  if (!cfg) return <p className="muted">Loading…</p>;

  return (
    <div className="grid" style={{ maxWidth: 560 }}>
      <h1 style={{ margin: 0 }}>Settings</h1>
      <p className="muted">Token stays in .env only (masked here).</p>
      {(
        [
          ["leetcode_username", "LeetCode username"],
          ["github_repo", "GitHub repo"],
          ["github_branch", "Branch"],
          ["llm_provider", "LLM provider"],
          ["llm_model", "LLM model"],
          ["ollama_base_url", "Ollama URL"],
        ] as const
      ).map(([k, label]) => (
        <label key={k} className="grid" style={{ gap: "0.25rem" }}>
          <span className="muted">{label}</span>
          <input
            value={String(cfg[k])}
            onChange={(e) => setCfg({ ...cfg, [k]: e.target.value })}
          />
        </label>
      ))}
      <label className="row">
        <input
          type="checkbox"
          checked={cfg.dry_run}
          onChange={(e) => setCfg({ ...cfg, dry_run: e.target.checked })}
        />
        Default dry-run
      </label>
      <p className="muted">GitHub token: {cfg.github_token_set ? "set" : "missing"}</p>
      {err && <p style={{ color: "var(--red)" }}>{err}</p>}
      <button className="primary" onClick={save} disabled={saving}>
        {saving ? "Saving…" : "Save"}
      </button>
      {msg && <p style={{ color: "var(--green)" }}>{msg}</p>}
    </div>
  );
}
