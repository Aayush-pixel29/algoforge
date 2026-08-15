import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Health, type Problem } from "../api";
import { StreakHeatmap } from "../components/StreakHeatmap";
import { InterviewCountdown } from "../components/InterviewCountdown";

export default function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [problem, setProblem] = useState<Problem | null>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [healthLoading, setHealthLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    api<Health>("/api/health", { signal: controller.signal })
      .then(setHealth)
      .catch((e) => {
        if (!controller.signal.aborted) setErr(String(e));
      })
      .finally(() => setHealthLoading(false));
    return () => controller.abort();
  }, []);

  async function scout(isRandom: boolean = false) {
    setLoading(true);
    setErr("");
    try {
      const data = await api<{ problem: Problem }>(`/api/scout${isRandom ? "?random=true" : ""}`);
      setProblem(data.problem);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid">
      <div className="page-header">
        <h1 style={{ margin: "0 0 0.25rem" }}>Mission Control</h1>
        <p className="muted">Overview / Good Morning! Keep forging your path.</p>
      </div>

      {healthLoading ? (
        <p className="muted">Loading status…</p>
      ) : (
        <div className="grid cols-3">
          <div className="card">
            <div className="card-header">
              <h3><span className="card-icon">🤖</span> Ollama Instance</h3>
              <span className={`status-indicator ${health?.ollama ? "ok" : "bad"}`}></span>
            </div>
            <div className="status-row">
              <span className="status-label">Status</span>
              <span className={`status-value ${health?.ollama ? "ok" : "bad"}`}>
                {health?.ollama ? "Online" : "Offline"}
              </span>
            </div>
            <div className="status-row">
              <span className="status-label">Model</span>
              <span className="status-value">{health?.llm || "—"}</span>
            </div>
          </div>
          <div className="card">
            <div className="card-header">
              <h3><span className="card-icon">💻</span> GitHub Integration</h3>
              <span className={`status-indicator ${health?.github_token ? "ok" : "bad"}`}></span>
            </div>
            <div className="status-row">
              <span className="status-label">Status</span>
              <span className={`status-value ${health?.github_token ? "ok" : "bad"}`}>
                {health?.github_token ? "Synced" : "No token"}
              </span>
            </div>
            <div className="status-row">
              <span className="status-label">Repo</span>
              <span className="status-value">{health?.github_repo || "—"}</span>
            </div>
          </div>
          <div className="card">
            <div className="card-header">
              <h3><span className="card-icon">🧑‍💻</span> Learner API</h3>
              <span className="status-indicator ok"></span>
            </div>
            <div className="status-row">
              <span className="status-label">User</span>
              <span className="status-value">@{health?.leetcode_username || "—"}</span>
            </div>
            <div className="status-row">
              <span className="status-label">Dry Run</span>
              <span className="status-value">{health?.dry_run ? "Enabled" : "Disabled"}</span>
            </div>
          </div>
        </div>
      )}

      <div className="grid cols-2" style={{ marginTop: "0.5rem" }}>
        <div className="card" style={{ padding: "1.5rem" }}>
          <h3 style={{ marginBottom: "1.5rem" }}>Commit Activity</h3>
          <StreakHeatmap />
        </div>
        <div className="card" style={{ padding: "1.5rem" }}>
          <h3 style={{ marginBottom: "1.5rem" }}>Interview Countdown</h3>
          <InterviewCountdown />
        </div>
      </div>

      {err && <div className="card" style={{ marginTop: "1.5rem", borderColor: "var(--red)" }}><p style={{ color: "var(--red)" }}>{err}</p></div>}

      <div className="card problem-card">
        <div className="card-header" style={{ marginBottom: "0.5rem" }}>
          <h3><span className="card-icon">⚡</span> Daily Challenge Scout</h3>
        </div>
        
        {!problem ? (
          <div className="problem-actions">
            <button className="primary" onClick={() => scout(false)} disabled={loading}>
              {loading ? "Scouting network..." : "Scout today's challenge"}
            </button>
            <Link to="/forge" style={{ flex: 1, display: "flex" }}>
              <button className="primary" style={{ width: "100%", background: "var(--bg-surface-2)", color: "var(--text)" }}>Forge manually</button>
            </Link>
          </div>
        ) : (
          <>
            <h2>{problem.problem_id}. {problem.title}</h2>
            <div className="meta">
              <span className={`pill ${problem.difficulty}`}>{problem.difficulty}</span>
              <span>Acceptance: {problem.acceptance_rate || "N/A"}</span>
            </div>
            <p className="desc">{problem.description_text.slice(0, 300)}...</p>
            
            <div className="row">
              {problem.topics.map(t => <span key={t} className="pill" style={{ background: "var(--bg-surface-2)", color: "var(--text)", borderColor: "var(--line)" }}>{t}</span>)}
            </div>

            <div className="problem-actions">
              <button className="primary" style={{ background: "var(--bg-surface-2)", color: "var(--text)" }} onClick={() => scout(true)} disabled={loading}>
                 {loading ? "Scouting…" : "Scout different"}
              </button>
              <Link to="/forge" style={{ flex: 1, display: "flex" }}>
                <button className="primary" style={{ width: "100%" }}>Forge this challenge</button>
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
