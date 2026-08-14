import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

type Ev = { stage: string; message: string; ts?: string };

export default function Forge() {
  const [slug, setSlug] = useState("");
  const [dryRun, setDryRun] = useState(true);
  const [running, setRunning] = useState(false);
  const [events, setEvents] = useState<Ev[]>([]);
  const [jobId, setJobId] = useState("");
  const [err, setErr] = useState("");
  const logRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);
  const nav = useNavigate();

  // Auto-scroll log
  useEffect(() => {
    logRef.current?.scrollTo(0, logRef.current.scrollHeight);
  }, [events]);

  // Cleanup EventSource on unmount
  useEffect(() => {
    return () => {
      esRef.current?.close();
    };
  }, []);

  async function start() {
    setErr("");
    setEvents([]);
    setRunning(true);
    // Close any previous SSE connection
    esRef.current?.close();
    try {
      const { job_id } = await api<{ job_id: string }>("/api/forge", {
        method: "POST",
        body: JSON.stringify({ slug: slug || null, dry_run: dryRun }),
      });
      setJobId(job_id);
      const es = new EventSource(`/api/forge/${job_id}/events`);
      esRef.current = es;
      es.onmessage = (m) => {
        const ev = JSON.parse(m.data) as Ev;
        if (ev.stage === "end") {
          es.close();
          esRef.current = null;
          setRunning(false);
          api<{ status: string; result?: { folder: string } }>(`/api/forge/${job_id}`).then((j) => {
            if (j.status === "done" && j.result?.folder) {
              nav(`/study/${j.result.folder}`);
            }
          });
          return;
        }
        setEvents((prev) => [...prev, ev]);
      };
      es.onerror = () => {
        es.close();
        esRef.current = null;
        setRunning(false);
        setErr("SSE connection lost");
      };
    } catch (e) {
      setErr(String(e));
      setRunning(false);
    }
  }

  const stages = ["scout", "brain", "artifacts", "commit", "done"];
  const last = events[events.length - 1]?.stage;

  return (
    <div className="grid">
      <div>
        <h1 style={{ margin: 0 }}>Forge Run</h1>
        <p className="muted">Solver → Tutor → Reviewer. CPU Ollama can take several minutes.</p>
      </div>

      <div className="card row">
        <input
          placeholder="optional slug (e.g. two-sum)"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          style={{ flex: 1, minWidth: 200 }}
        />
        <label className="row" style={{ gap: "0.4rem" }}>
          <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
          Dry-run (no GitHub push)
        </label>
        <button className="primary" onClick={start} disabled={running}>
          {running ? "Forging…" : "Start forge"}
        </button>
      </div>

      <div className="row">
        {stages.map((s) => (
          <span key={s} className={`pill ${last === s ? "ok" : ""}`}>{s}</span>
        ))}
        {jobId && <span className="muted mono">job {jobId}</span>}
      </div>

      {err && <p style={{ color: "var(--red)" }}>{err}</p>}

      <div className="log mono" ref={logRef}>
        {events.length === 0 && <div className="muted">Waiting for events…</div>}
        {events.map((e, i) => (
          <div key={i}>
            <span className="muted">[{e.stage}]</span> {e.message}
          </div>
        ))}
      </div>
    </div>
  );
}
