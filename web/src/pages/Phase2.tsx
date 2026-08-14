import { useState } from "react";
import { Beaker, Sparkles, Send } from "lucide-react";
import { api, type Problem } from "../api";

export default function Phase2() {
  const [contestId, setContestId] = useState("158");
  const [index, setIndex] = useState("A");
  const [loading, setLoading] = useState(false);
  const [problem, setProblem] = useState<Problem | null>(null);
  const [err, setErr] = useState("");

  const [agentLoading, setAgentLoading] = useState(false);
  const [agentResponse, setAgentResponse] = useState("");

  async function scoutCodeforces() {
    setLoading(true);
    setErr("");
    setProblem(null);
    setAgentResponse("");
    try {
      const data = await api<{ problem: Problem }>(`/api/phase2/codeforces?contest_id=${contestId}&index=${index}`);
      setProblem(data.problem);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function spawnResearchAgent() {
    if (!problem) return;
    setAgentLoading(true);
    setAgentResponse("Spawning CrewAI Research Sub-Agent...\nAnalyzing Codeforces problem constraints...\n");
    try {
      // Simulate sub-agent response or call real endpoint if we have one
      const data = await api<{ response: string }>(`/api/phase2/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem_id: problem.problem_id, title: problem.title })
      });
      setAgentResponse((prev) => prev + "\n" + data.response);
    } catch (e) {
      setAgentResponse((prev) => prev + "\n[Error]: " + String(e));
    } finally {
      setAgentLoading(false);
    }
  }

  return (
    <div className="grid">
      <div>
        <h1 style={{ margin: "0 0 0.25rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Beaker color="var(--accent)" /> Phase 2 Sandbox
        </h1>
        <p className="muted">Test multi-platform fetching (Codeforces) and autonomous Research Sub-Agents.</p>
      </div>

      <div className="card">
        <h3>Fetch Codeforces Problem</h3>
        <div className="row" style={{ marginTop: "1rem" }}>
          <input 
            type="text" 
            placeholder="Contest ID (e.g. 158)" 
            value={contestId} 
            onChange={e => setContestId(e.target.value)} 
            style={{ width: "150px" }}
          />
          <input 
            type="text" 
            placeholder="Index (e.g. A)" 
            value={index} 
            onChange={e => setIndex(e.target.value)} 
            style={{ width: "100px" }}
          />
          <button className="primary" onClick={scoutCodeforces} disabled={loading || !contestId || !index}>
            {loading ? "Scouting..." : "Scout Codeforces"}
          </button>
        </div>
        {err && <p style={{ color: "var(--red)", marginTop: "1rem" }}>{err}</p>}
      </div>

      {problem && (
        <div className="split">
          <div className="card" style={{ display: "flex", flexDirection: "column" }}>
            <div className="row" style={{ marginBottom: "0.5rem" }}>
              <strong>{problem.problem_id}. {problem.title}</strong>
              <span className={`pill ${problem.difficulty}`}>{problem.difficulty || "unknown"}</span>
            </div>
            <p className="muted" style={{ fontSize: "0.9rem" }}>
              {problem.topics?.join(" · ")}
            </p>
            <div className="log" style={{ flexGrow: 1, marginTop: "1rem", whiteSpace: "pre-wrap" }}>
              {problem.description_text}
            </div>
            <div className="row" style={{ marginTop: "1rem" }}>
              <a href={problem.url} target="_blank" rel="noreferrer" className="pill ok">Open on Codeforces ↗</a>
            </div>
          </div>

          <div className="card" style={{ display: "flex", flexDirection: "column", border: "1px solid var(--accent)" }}>
            <h3><Sparkles size={16} style={{ display: "inline", verticalAlign: "middle" }} color="var(--accent)"/> Research Sub-Agent</h3>
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              Deploy an AI sub-agent to analyze constraints and find edge cases before coding.
            </p>
            
            <button 
              style={{ background: "rgba(59, 130, 246, 0.1)", color: "var(--accent)", border: "1px solid rgba(59, 130, 246, 0.3)", marginTop: "1rem" }}
              onClick={spawnResearchAgent}
              disabled={agentLoading}
            >
              {agentLoading ? "Agent is thinking..." : <><Send size={16}/> Dispatch Sub-Agent</>}
            </button>

            {agentResponse && (
              <div className="log" style={{ marginTop: "1rem", flexGrow: 1, fontFamily: "monospace", color: "var(--green)" }}>
                {agentResponse}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
