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

  async function scout() {
    setLoading(true);
    setErr("");
    try {
      const data = await api<{ problem: Problem }>("/api/scout");
      setProblem(data.problem);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid">
      <div>
        <h1 style={{ margin: "0 0 0.25rem" }}>Mission Control</h1>
        <p className="muted">Fetch today's challenge, forge with Gemini, push streak.</p>
      </div>

      <div className="grid cols-2" style={{ gap: "1rem", marginBottom: "1rem", gridTemplateColumns: "2fr 1fr" }}>
        <StreakHeatmap />
        <InterviewCountdown />
      </div>

      {healthLoading ? (
        <p className="muted">Loading status…</p>
      ) : (
        <div className="grid cols-3">
          <div className="card">
            <h3>Ollama</h3>
            <span className={`pill ${health?.ollama ? "ok" : "bad"}`}>
              {health?.ollama ? "online" : "offline"}
            </span>
            <p className="muted mono" style={{ fontSize: "0.8rem", marginTop: "0.5rem" }}>
              {health?.llm || "—"}
            </p>
          </div>
          <div className="card">
            <h3>GitHub</h3>
            <span className={`pill ${health?.github_token ? "ok" : "bad"}`}>
              {health?.github_token ? "token set" : "no token"}
            </span>
            <p className="muted" style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>
              {health?.github_repo || "—"}
            </p>
          </div>
          <div className="card">
            <h3>Learner</h3>
            <p style={{ margin: 0 }}>@{health?.leetcode_username || "—"}</p>
          </div>
        </div>
      )}

      <div className="row">
        <button className="primary" onClick={scout} disabled={loading}>
          {loading ? "Scouting…" : "Scout daily"}
        </button>
        <Link to="/forge"><button className="primary">Forge today</button></Link>
      </div>

      {err && <p style={{ color: "var(--red)" }}>{err}</p>}

      {problem && (
        <div className="card">
          <div className="row" style={{ marginBottom: "0.5rem" }}>
            <strong>{problem.problem_id}. {problem.title}</strong>
            <span className={`pill ${problem.difficulty}`}>{problem.difficulty}</span>
          </div>
          <p className="muted" style={{ fontSize: "0.9rem" }}>
            {problem.topics.join(" · ")}
          </p>
          <p style={{ maxHeight: 160, overflow: "auto", fontSize: "0.9rem" }}>
            {problem.description_text.slice(0, 600)}…
          </p>
          <a href={problem.url} target="_blank" rel="noreferrer">Open on LeetCode</a>
        </div>
      )}
    </div>
  );
}
