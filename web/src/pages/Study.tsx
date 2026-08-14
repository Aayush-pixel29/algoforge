import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { api } from "../api";

export default function Study() {
  const { folder: param } = useParams();
  const [folder, setFolder] = useState(param || "");
  const [readme, setReadme] = useState("");
  const [code, setCode] = useState("");
  const [items, setItems] = useState<{ folder: string }[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  // Load artifact list
  useEffect(() => {
    const controller = new AbortController();
    api<{ items: { folder: string }[] }>("/api/artifacts", { signal: controller.signal })
      .then((d) => {
        setItems(d.items);
        if (!param && d.items[0]) setFolder(d.items[0].folder);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setErr(String(e));
      });
    return () => controller.abort();
  }, [param]);

  // Sync folder from URL param
  useEffect(() => {
    if (param) setFolder(param);
  }, [param]);

  // Load artifact content when folder changes
  useEffect(() => {
    if (!folder) return;
    const controller = new AbortController();
    // Clear stale data before loading
    setReadme("");
    setCode("");
    setLoading(true);
    setErr("");
    api<{ readme_markdown: string; solution_code: string }>(`/api/artifacts/${folder}`, { signal: controller.signal })
      .then((d) => {
        setReadme(d.readme_markdown);
        setCode(d.solution_code);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setErr(String(e));
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [folder]);

  return (
    <div className="grid">
      <div className="row">
        <h1 style={{ margin: 0, flex: 1 }}>Study</h1>
        <select value={folder} onChange={(e) => setFolder(e.target.value)}>
          {items.map((i) => (
            <option key={i.folder} value={i.folder}>{i.folder}</option>
          ))}
        </select>
        <button className="ghost" onClick={() => navigator.clipboard.writeText(code)}>Copy code</button>
      </div>
      {err && <p style={{ color: "var(--red)" }}>{err}</p>}
      {!folder && <p className="muted">No forged packs yet. Run Forge first.</p>}
      {folder && loading && <p className="muted">Loading…</p>}
      {folder && !loading && (
        <div className="split">
          <div className="panel md">
            <ReactMarkdown>{readme || "_No README_"}</ReactMarkdown>
          </div>
          <div className="panel">
            <pre className="mono">{code || "// no solution"}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
