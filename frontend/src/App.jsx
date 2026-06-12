import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function Badge({ text }) {
  if (!text) return <span className="badge muted">—</span>;

  const cls =
    text === "FAITHFUL"
      ? "badge green"
      : text === "NOT_FAITHFUL"
        ? "badge red"
        : "badge blue";

  return <span className={cls}>{text}</span>;
}

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [routes, setRoutes] = useState([]);
  const [sources, setSources] = useState([]);
  const [faithfulness, setFaithfulness] = useState("");
  const [rewrittenQuestion, setRewrittenQuestion] = useState("");
  const [domainOutputs, setDomainOutputs] = useState({});
  const [blocked, setBlocked] = useState(false);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [logs, setLogs] = useState([]);
  const [search, setSearch] = useState("");

  const fetchLogs = async () => {
    const res = await axios.get(`${API_BASE}/logs`);
    setLogs((res.data.logs || []).reverse());
  };

  const fetchMetrics = async () => {
    const res = await axios.get(`${API_BASE}/metrics`);
    setMetrics(res.data);
  };

  useEffect(() => {
    fetchLogs();
    fetchMetrics();
  }, []);

  const askQuestion = async () => {
    if (!question.trim()) return;

    setLoading(true);
    setAnswer("");
    setRoutes([]);
    setSources([]);
    setFaithfulness("");
    setRewrittenQuestion("");
    setDomainOutputs({});
    setBlocked(false);

    try {
      const res = await axios.post(`${API_BASE}/ask`, { question });

      setAnswer(res.data.answer || "");
      setRoutes(res.data.routes || []);
      setSources(res.data.sources || []);
      setFaithfulness(res.data.faithfulness || "");
      setRewrittenQuestion(res.data.rewritten_question || "");
      setDomainOutputs(res.data.domain_outputs || {});
      setBlocked(res.data.blocked || false);

      await fetchLogs();
      await fetchMetrics();
    } catch {
      setAnswer("Backend API connection failed.");
      setBlocked(true);
    }

    setLoading(false);
  };

  const sendFeedback = async (feedback) => {
    await axios.post(`${API_BASE}/feedback`, {
      question,
      answer,
      feedback,
    });

    await fetchMetrics();
  };

  const filteredLogs = useMemo(() => {
    if (!search.trim()) return logs;
    return logs.filter((log) =>
      `${log.question} ${log.answer} ${log.routes?.join(" ")}`
        .toLowerCase()
        .includes(search.toLowerCase())
    );
  }, [logs, search]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="logo">T</div>
          <div>
            <h1>
              TECHNOVA <span>SOLUTIONS</span>
            </h1>
            <p>Enterprise Policy Assistant</p>
          </div>
        </div>

        <div className="features">
          <span>Multi-Agent RAG</span>
          <b>•</b>
          <span>Guardrails</span>
          <b>•</b>
          <span>Faithfulness</span>
          <b>•</b>
          <span>Phoenix Ready</span>
        </div>

        <button className="icon-btn">☼</button>
      </header>

      <section className="metrics">
        <div className="metric-card">
          <div className="metric-icon blue">▣</div>
          <div>
            <h2>{metrics?.total_questions ?? 0}</h2>
            <p>Total Questions</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon green">✓</div>
          <div>
            <h2>{metrics?.faithful_count ?? 0}</h2>
            <p>Faithful</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon red">✕</div>
          <div>
            <h2>{metrics?.not_faithful_count ?? 0}</h2>
            <p>Not Faithful</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon blue">👍</div>
          <div>
            <h2>{metrics?.positive_feedback ?? 0}</h2>
            <p>Positive Feedback</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon red">👎</div>
          <div>
            <h2>{metrics?.negative_feedback ?? 0}</h2>
            <p>Negative Feedback</p>
          </div>
        </div>
      </section>

      <main className="main-grid">
        <section className="panel ask-panel">
          <div className="section-title">
            <span>💬</span>
            <div>
              <h2>Ask Policy Assistant</h2>
              <p>Ask any question related to TechNova company policies.</p>
            </div>
          </div>

          <div className="textarea-wrap">
            <textarea
              value={question}
              maxLength={2000}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Type your company policy question here..."
            />
            <span>{question.length} / 2000</span>
          </div>

          <button className="primary-btn" onClick={askQuestion} disabled={loading}>
            {loading ? "Thinking..." : "➤ Ask Assistant"}
          </button>

          {answer && (
            <div className={blocked ? "answer-box blocked" : "answer-box"}>
              <h3>{blocked ? "Blocked by Guardrails" : "Final Answer"}</h3>
              <p>{answer}</p>

              {!blocked && (
                <div className="feedback-row">
                  <button onClick={() => sendFeedback("positive")}>👍 Helpful</button>
                  <button onClick={() => sendFeedback("negative")}>👎 Not Helpful</button>
                </div>
              )}
            </div>
          )}
        </section>

        <aside className="panel trace-panel">
          <div className="section-title">
            <span>〽</span>
            <h2>Trace Summary</h2>
          </div>

          <div className="trace-item">
            <span>✎</span>
            <div>
              <label>Rewritten Question</label>
              <p>{rewrittenQuestion || "—"}</p>
            </div>
          </div>

          <div className="trace-item">
            <span>⌘</span>
            <div>
              <label>Routes</label>
              <p>{routes.length ? routes.join(", ") : "—"}</p>
            </div>
          </div>

          <div className="trace-item">
            <span>🛡</span>
            <div>
              <label>Faithfulness</label>
              <p>
                <Badge text={faithfulness || "—"} />
              </p>
            </div>
          </div>

          <div className="trace-item">
            <span>□</span>
            <div>
              <label>Sources</label>
              <p>{sources.length ? sources.map((s) => s.split("/").pop()).join(", ") : "—"}</p>
            </div>
          </div>
        </aside>
      </main>

      {Object.keys(domainOutputs).length > 0 && (
        <section className="panel agents-panel">
          <div className="section-title">
            <span>🤖</span>
            <div>
              <h2>Domain Agent Outputs</h2>
              <p>Specialist responses before final synthesis.</p>
            </div>
          </div>

          <div className="agent-grid">
            {Object.entries(domainOutputs).map(([route, output]) => (
              <div className="agent-card" key={route}>
                <Badge text={route} />
                <p>{output}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="panel history-panel">
        <div className="history-head">
          <div className="section-title">
            <span>↺</span>
            <div>
              <h2>History</h2>
              <p>View all your previous questions and answers.</p>
            </div>
          </div>

          <div className="history-actions">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search history..."
            />
            <button>⚱ Filter</button>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Question</th>
                <th>Answer</th>
                <th>Routes</th>
                <th>Faithfulness</th>
                <th>Sources</th>
              </tr>
            </thead>

            <tbody>
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty">
                    No history found.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td>{log.question}</td>
                    <td>{log.answer}</td>
                    <td>
                      {(log.routes || []).length
                        ? log.routes.map((r) => <Badge key={r} text={r} />)
                        : "—"}
                    </td>
                    <td>
                      <Badge text={log.faithfulness || "N/A"} />
                    </td>
                    <td>
                      {(log.retrieved_sources || [])
                        .map((s) => s.split("/").pop())
                        .join(", ") || "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <footer>© 2025 TechNova Solutions. All rights reserved.</footer>
    </div>
  );
}

export default App;