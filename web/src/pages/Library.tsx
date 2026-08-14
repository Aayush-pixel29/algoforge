import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

type Item = { folder: string; has_readme: boolean; solution: string | null };

export default function Library() {
  const [items, setItems] = useState<Item[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    api<{ items: Item[] }>("/api/artifacts", { signal: controller.signal })
      .then((d) => setItems(d.items))
      .catch((e) => {
        if (!controller.signal.aborted) setErr(String(e));
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  return (
    <div className="grid">
      <div>
        <h1 style={{ margin: 0 }}>Library</h1>
        <p className="muted">Local forged packs under output/</p>
      </div>
      {err && <p style={{ color: "var(--red)" }}>{err}</p>}
      {loading ? (
        <p className="muted">Loading…</p>
      ) : (
        <div className="card list">
          {items.length === 0 && <p className="muted">Empty — forge a problem first.</p>}
          {items.map((i) => (
            <Link key={i.folder} to={`/study/${i.folder}`}>
              <button>
                <strong className="mono">{i.folder}</strong>
                <span className="muted"> · {i.solution || "no py"}</span>
              </button>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
