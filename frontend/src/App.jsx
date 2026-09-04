import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const tabs = ["Overview", "Live wall", "Events", "Taxonomy", "Assistant", "Responsible AI", "Ingest"];

export default function App() {
  const [tab, setTab] = useState("Overview");
  const [summary, setSummary] = useState(null);
  const [events, setEvents] = useState([]);
  const [tax, setTax] = useState([]);
  const [q, setQ] = useState("How much damage exposure today?");
  const [chat, setChat] = useState([]);
  const [ingest, setIngest] = useState(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setSummary(await fetch("/api/summary").then((r) => r.json()));
    setEvents(await fetch("/api/events").then((r) => r.json()));
    setTax(await fetch("/api/taxonomy").then((r) => r.json()));
  }

  useEffect(() => {
    refresh();
  }, []);

  async function send() {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    }).then((r) => r.json());
    setChat((c) => [...c, { role: "user", text: q }, { role: "bot", text: res.text }]);
  }

  async function upload(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy(true);
    const fd = new FormData();
    fd.append("file", f);
    const res = await fetch("/api/ingest", { method: "POST", body: fd }).then((r) => r.json());
    setIngest(res);
    setBusy(false);
    await refresh();
    setTab("Events");
  }

  async function runDemo() {
    setBusy(true);
    const res = await fetch("/api/ingest-demo", { method: "POST" }).then((r) => r.json());
    setIngest(res);
    setBusy(false);
    await refresh();
    setTab("Live wall");
  }

  async function verdict(id, v) {
    await fetch("/api/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_id: id, verdict: v }),
    });
    await refresh();
  }

  const bars = summary
    ? Object.entries(summary.by_behaviour || {}).map(([k, v]) => ({ name: k.replaceAll("_", " "), n: v }))
    : [];

  return (
    <div className="shell">
      <aside className="nav">
        <div className="brand">
          SAHA<span>AYAK</span>
        </div>
        <div className="tag">Warehouse handling co-pilot · tracklets, not pixels</div>
        {tabs.map((t) => (
          <button key={t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
        <p className="tiny" style={{ marginTop: 28 }}>
          LLM never sees frames. Behaviour engine consumes TrackFeatures only.
        </p>
      </aside>
      <main className="main">
        {tab === "Overview" && summary && (
          <>
            <div className="headline">{summary.headline}</div>
            <div className="journey">
              {["Activity", "Video", "Tracklets", "FSM", "Risk", "Alert", "Prevention"].map((s, i) => (
                <i key={s} className={i === 6 ? "hi" : ""}>
                  {s}
                </i>
              ))}
            </div>
            <div className="kpis">
              <div className="card">
                <h3>Events</h3>
                <div className="n">{summary.events}</div>
              </div>
              <div className="card">
                <h3>High / critical</h3>
                <div className="n">{summary.high_risk}</div>
              </div>
              <div className="card">
                <h3>Damage exposure</h3>
                <div className="n">₹{(summary.exposure_inr || 0).toLocaleString("en-IN")}</div>
              </div>
              <div className="card">
                <h3>Honesty mix</h3>
                <div className="tiny">
                  {Object.entries(summary.by_honesty || {})
                    .map(([k, v]) => `${k} ${v}`)
                    .join(" · ")}
                </div>
              </div>
            </div>
            <div className="grid2">
              <div className="card">
                <h3>Behaviours this shift</h3>
                <div style={{ height: 260 }}>
                  <ResponsiveContainer>
                    <BarChart data={bars}>
                      <XAxis dataKey="name" tick={{ fill: "#8fa3b5", fontSize: 10 }} interval={0} angle={-25} />
                      <YAxis tick={{ fill: "#8fa3b5", fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="n" fill="#e24c3a" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="card">
                <h3>Bay heat</h3>
                {Object.entries(summary.by_bay || {}).map(([k, v]) => (
                  <p key={k}>
                    {k} — <b>{v}</b>
                  </p>
                ))}
              </div>
            </div>
          </>
        )}

        {tab === "Live wall" && (
          <div className="card">
            <h3>Live / last ingest overlay</h3>
            <p className="tiny">
              Boxes are drawn on the evidence clip. Run the synthetic dock clip or upload Godrej MP4.
            </p>
            <button className="primary" disabled={busy} onClick={runDemo}>
              {busy ? "Inferring…" : "Run synthetic DROP clip"}
            </button>
            {ingest && (
              <>
                <p>
                  Backend {ingest.backend} · {ingest.frames} frames · {ingest.events?.length || 0} events
                </p>
                <pre className="tiny">{JSON.stringify(ingest.events, null, 2)}</pre>
              </>
            )}
          </div>
        )}

        {tab === "Events" && (
          <div className="card">
            <h3>Event store — three-state honesty · human review</h3>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Bay</th>
                  <th>Behaviour</th>
                  <th>SKU</th>
                  <th>Risk</th>
                  <th>J</th>
                  <th>₹</th>
                  <th>State</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id} style={{ opacity: e.dismissed ? 0.4 : 1 }}>
                    <td>{e.id}</td>
                    <td>{e.bay}</td>
                    <td>{e.behaviour}</td>
                    <td>{e.product_class}</td>
                    <td>
                      <span className={`band ${e.risk_level}`}>{e.risk_level}</span>
                    </td>
                    <td>{e.impact_j}</td>
                    <td>{e.exposure_inr}</td>
                    <td className="honesty">{e.state}</td>
                    <td>
                      <button onClick={() => verdict(e.id, "confirm")}>confirm</button>
                      <button onClick={() => verdict(e.id, "dismiss")}>down</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "Taxonomy" && (
          <div className="tax">
            {tax.map((b, i) => (
              <div className="card" key={b.id}>
                <h3>
                  {i + 1}. {b.name}
                </h3>
                <p>Coach: {b.good}</p>
              </div>
            ))}
          </div>
        )}

        {tab === "Assistant" && (
          <div className="card">
            <h3>Co-pilot — tools over events, never pixels</h3>
            <div className="chatlog">
              {chat.map((m, i) => (
                <div key={i} className={`bubble ${m.role}`}>
                  <b>{m.role === "user" ? "Supervisor" : "Sahaayak"}:</b> {m.text}
                </div>
              ))}
            </div>
            <div className="row">
              <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} />
              <button className="primary" onClick={send}>
                Ask
              </button>
            </div>
          </div>
        )}

        {tab === "Responsible AI" && (
          <div className="grid2">
            <div className="card">
              <h3>Anonymous by default</h3>
              <p>Faces stay off the event record. Handler-IDs are clip-local. Reporting is by bay / shift / process.</p>
            </div>
            <div className="card">
              <h3>Three-state honesty</h3>
              <p>OBSERVED → POTENTIAL_RISK → CONFIRMED_DAMAGE. Explanations are templates, not LLM prose.</p>
            </div>
          </div>
        )}

        {tab === "Ingest" && (
          <div className="card">
            <h3>Upload a warehouse clip</h3>
            <p className="tiny">
              Perception (YOLO if installed, else MOG2) → TrackFeatures → 10 FSM detectors → risk → SQLite. YOLO is
              optional; the contract is the tracklet stream.
            </p>
            <input type="file" accept="video/*" onChange={upload} disabled={busy} />
            {busy && <p>Running temporal reasoning…</p>}
            {ingest && <pre className="tiny">{JSON.stringify({ ...ingest, overlays: ingest.overlays?.slice(0, 3) }, null, 2)}</pre>}
          </div>
        )}
      </main>
    </div>
  );
}
