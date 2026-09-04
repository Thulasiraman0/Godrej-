import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const tabs = ["Overview", "Events", "Taxonomy", "Assistant", "Responsible AI", "Ingest"];

export default function App() {
  const [tab, setTab] = useState("Overview");
  const [summary, setSummary] = useState(null);
  const [events, setEvents] = useState([]);
  const [tax, setTax] = useState([]);
  const [q, setQ] = useState("How much damage exposure today in Bay-A?");
  const [chat, setChat] = useState([]);
  const [ingest, setIngest] = useState(null);

  useEffect(() => {
    fetch("/api/summary").then((r) => r.json()).then(setSummary);
    fetch("/api/events").then((r) => r.json()).then(setEvents);
    fetch("/api/taxonomy").then((r) => r.json()).then(setTax);
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
    const fd = new FormData();
    fd.append("file", f);
    const res = await fetch("/api/ingest", { method: "POST", body: fd }).then((r) => r.json());
    setIngest(res);
    const s = await fetch("/api/summary").then((r) => r.json());
    setSummary(s);
    setEvents(await fetch("/api/events").then((r) => r.json()));
  }

  const bars = summary
    ? Object.entries(summary.by_behaviour).map(([k, v]) => ({ name: k.replaceAll("_", " "), n: v }))
    : [];

  return (
    <div className="shell">
      <aside className="nav">
        <div className="brand">SAHA<span>AYAK</span></div>
        <div className="tag">Warehouse handling co-pilot · Godrej × graVITas ’26</div>
        {tabs.map((t) => (
          <button key={t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
        <p className="tiny" style={{ marginTop: 28 }}>
          We score bays, shifts and processes — not named employees.
        </p>
      </aside>
      <main className="main">
        {tab === "Overview" && summary && (
          <>
            <div className="headline">{summary.headline}</div>
            <div className="journey">
              {["Activity", "Video", "AI understanding", "Risk", "Alert", "Intervention", "Prevention"].map(
                (s, i) => (
                  <i key={s} className={i === 6 ? "hi" : ""}>
                    {s}
                  </i>
                )
              )}
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
                <div className="n">₹{summary.exposure_inr.toLocaleString("en-IN")}</div>
              </div>
              <div className="card">
                <h3>Honesty mix</h3>
                <div className="tiny">
                  {Object.entries(summary.by_honesty)
                    .map(([k, v]) => `${k.replaceAll("_", " ")} ${v}`)
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
                      <XAxis dataKey="name" tick={{ fill: "#8fa3b5", fontSize: 10 }} interval={0} angle={-20} />
                      <YAxis tick={{ fill: "#8fa3b5", fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="n" fill="#e24c3a" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="card">
                <h3>By bay</h3>
                {Object.entries(summary.by_bay).map(([k, v]) => (
                  <p key={k}>
                    {k} — <b>{v}</b>
                  </p>
                ))}
                <p className="tiny">Anonymous Handler-IDs are clip-local. Faces are blurred before storage.</p>
              </div>
            </div>
          </>
        )}

        {tab === "Events" && (
          <div className="card">
            <h3>Event store — three-state honesty</h3>
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Bay</th>
                  <th>Behaviour</th>
                  <th>SKU</th>
                  <th>Risk</th>
                  <th>J</th>
                  <th>₹</th>
                  <th>State</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id}>
                    <td>{e.ts?.slice(11, 16) || e.ts}</td>
                    <td>{e.bay}</td>
                    <td>{e.behaviour.replaceAll("_", " ")}</td>
                    <td>{e.product_class}</td>
                    <td>
                      <span className={`band ${e.band}`}>{e.band}</span>
                    </td>
                    <td>{e.impact_j}</td>
                    <td>{e.exposure_inr}</td>
                    <td className="honesty">{e.honesty.replaceAll("_", " ")}</td>
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
                <p className="tiny">{b.detection}</p>
                <p>Coach: {b.good}</p>
              </div>
            ))}
          </div>
        )}

        {tab === "Assistant" && (
          <div className="card">
            <h3>Co-pilot — tool-calling over events, never pixels</h3>
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
              <p>Faces are blurred at the edge before any frame is stored. A person is Handler-A inside one clip only. Identity is never persisted across clips.</p>
              <p>Reporting is by bay / shift / process. One toggle: a supervisor may attribute an event to a person only after human review.</p>
            </div>
            <div className="card">
              <h3>Three-state honesty</h3>
              <p>Observed behaviour → potential risk → confirmed damage. We never claim a product was damaged without post-impact evidence (deformation, spill, no return to motion).</p>
              <p>Every Critical card has a confidence bar and Human review required.</p>
            </div>
          </div>
        )}

        {tab === "Ingest" && (
          <div className="card">
            <h3>Run a clip through the motion + FSM pipeline</h3>
            <p className="tiny">YOLO is optional. This path uses MOG2 blobs + the same 10-behaviour FSM so a demo never depends on a weight file.</p>
            <input type="file" accept="video/*" onChange={upload} />
            {ingest && (
              <pre className="tiny">{JSON.stringify(ingest, null, 2)}</pre>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
