import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import java from 'react-syntax-highlighter/dist/esm/languages/prism/java';
import vscDarkPlus from 'react-syntax-highlighter/dist/esm/styles/prism/vsc-dark-plus';
import { api } from "../api";
import { Check, Copy, AlertCircle } from "lucide-react";

SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('java', java);

interface Solution {
  name: string;
  code: string;
}

interface Artifacts {
  folder: string;
  readme_markdown: string;
  solutions: { [lang: string]: Solution };
  problem_text: string;
}

export default function Study() {
  const { folder: param } = useParams();
  const [folder, setFolder] = useState(param || "");
  const [data, setData] = useState<Artifacts | null>(null);
  const [items, setItems] = useState<{ folder: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [err, setErr] = useState("");
  const [activeTab, setActiveTab] = useState<string>("python");

  useEffect(() => {
    api<{ items: { folder: string }[] }>("/api/artifacts")
      .then((d) => {
        setItems(d.items);
        if (!param && d.items[0]) setFolder(d.items[0].folder);
      })
      .catch((e) => setErr(String(e)));
  }, [param]);

  useEffect(() => {
    if (param) setFolder(param);
  }, [param]);

  useEffect(() => {
    if (!folder) return;
    setLoading(true);
    setErr("");
    setData(null);
    api<Artifacts>(`/api/artifacts/${folder}`)
      .then(setData)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [folder]);

  const activeSolution = data?.solutions?.[activeTab];

  const handleCopy = () => {
    if (!activeSolution) return;
    navigator.clipboard.writeText(activeSolution.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="grid">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1 style={{ margin: 0, flex: 1, display: "flex", alignItems: "center", gap: "0.5rem" }}>
          Study Deck
        </h1>
        
        <select value={folder} onChange={(e) => setFolder(e.target.value)} style={{ minWidth: "250px" }}>
          {items.map((i) => (
            <option key={i.folder} value={i.folder}>{i.folder}</option>
          ))}
        </select>

        <button onClick={handleCopy} className="primary" disabled={!activeSolution}>
          {copied ? <Check size={16} /> : <Copy size={16} />} 
          {copied ? "Copied!" : "Copy Code"}
        </button>
      </div>

      {err && <div className="card" style={{ background: "var(--hard-bg)", borderColor: "var(--red)" }}>
        <AlertCircle size={20} color="var(--red)" style={{ display: "inline", verticalAlign: "middle", marginRight: "0.5rem" }}/>
        <span style={{ color: "var(--red)" }}>{err}</span>
      </div>}
      
      {!folder && !loading && <p className="muted">No forged packs yet. Go to Forge Studio first.</p>}
      {loading && folder && <p className="muted">Loading artifacts for {folder}...</p>}

      {!loading && data && (
        <div className="split">
          {/* Left Pane: Markdown Tutor */}
          <div className="panel md">
            <ReactMarkdown
              components={{
                code({node, className, children, ...props}) {
                  const match = /language-(\w+)/.exec(className || '')
                  return match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus as any}
                      language={match[1]}
                      PreTag="div"
                      {...props as any}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  )
                }
              }}
            >
              {data.readme_markdown || "*No README generated.*"}
            </ReactMarkdown>
          </div>

          {/* Right Pane: Code Viewer */}
          <div className="panel" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ background: "var(--bg-surface-2)", borderBottom: "1px solid var(--line)", display: 'flex' }}>
                {Object.keys(data.solutions || {}).map((lang) => (
                  <div 
                    key={lang}
                    onClick={() => setActiveTab(lang)}
                    style={{
                      padding: "0.75rem 1rem",
                      cursor: "pointer",
                      fontWeight: 600,
                      color: activeTab === lang ? "var(--accent)" : "var(--muted)",
                      borderBottom: activeTab === lang ? "2px solid var(--accent)" : "2px solid transparent"
                    }}
                  >
                    <span className="mono" style={{ fontSize: "0.85rem" }}>
                      {data.solutions[lang].name}
                    </span>
                  </div>
                ))}
            </div>
            <div style={{ flexGrow: 1, overflow: 'auto', background: "#1e1e1e" }}>
              <SyntaxHighlighter
                language={activeTab}
                style={vscDarkPlus as any}
                showLineNumbers={true}
                customStyle={{ margin: 0, padding: '1rem', background: 'transparent', fontSize: '0.85rem' }}
              >
                {activeSolution?.code || "# No code generated"}
              </SyntaxHighlighter>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
