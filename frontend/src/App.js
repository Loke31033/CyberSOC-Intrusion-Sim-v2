// src/App.js
import React, { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [alerts, setAlerts] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [filter, setFilter] = useState("ALL");
  const [status, setStatus] = useState({});
  const [notes, setNotes] = useState({});
  const [lastUpdated, setLastUpdated] = useState("");

  /* ================= FETCH ================= */

  const fetchSOCData = async () => {
    const [a, t] = await Promise.all([
      axios.get("http://127.0.0.1:5000/api/alerts"),
      axios.get("http://127.0.0.1:5000/api/timeline"),
    ]);
    setAlerts(a.data || []);
    setTimeline(t.data || []);
    setLastUpdated(new Date().toLocaleTimeString());
  };

  useEffect(() => {
    fetchSOCData();
    const interval = setInterval(fetchSOCData, 10000);
    return () => clearInterval(interval);
  }, []);

  /* ================= FILTER & SORT ================= */

  const severityRank = { HIGH: 3, MEDIUM: 2, LOW: 1 };

  const visibleAlerts = alerts
    .filter(a => filter === "ALL" || a.source === filter)
    .sort((a, b) => severityRank[b.severity] - severityRank[a.severity]);

  /* ================= UI HELPERS ================= */

  const sevColor = s =>
    s === "HIGH" ? "#dc2626" : s === "MEDIUM" ? "#f59e0b" : "#22c55e";

  const card = {
    background: "#141b2d",
    borderRadius: "12px",
    padding: "16px",
    marginBottom: "20px",
    boxShadow: "0 0 14px rgba(0,255,255,0.12)",
  };

  /* ================= UI ================= */

  return (
    <div style={{ background: "#0a0f1c", minHeight: "100vh", color: "#e5e7eb" }}>

      {/* ===== SOC HEADER ===== */}
      <header style={{
        background: "#020617",
        padding: "14px 24px",
        borderBottom: "1px solid #1f2937",
        display: "flex",
        justifyContent: "space-between"
      }}>
        <div>
          <strong style={{ color: "#00e0ff" }}>Security Operations Center</strong>
          <div style={{ fontSize: "12px", color: "#9ca3af" }}>
            Unified Threat Monitoring • Production
          </div>
        </div>
        <div style={{ fontSize: "12px", color: "#22c55e" }}>
          ● Live • Last update {lastUpdated}
        </div>
      </header>

      <div style={{ padding: "20px" }}>

        {/* ===== KPI BAR ===== */}
        <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
          <div style={card}><h2>{alerts.length}</h2><p>Open Incidents</p></div>
          <div style={card}><h2>{alerts.filter(a => a.severity === "HIGH").length}</h2><p>High Severity</p></div>
          <div style={card}><h2>{alerts.filter(a => a.source === "EMAIL").length}</h2><p>Email Threats</p></div>
        </div>

        {/* ===== FILTER ===== */}
        <div style={{ margin: "20px 0" }}>
          {["ALL", "LOG", "EMAIL"].map(f => (
            <button key={f}
              onClick={() => setFilter(f)}
              style={{
                marginRight: "10px",
                padding: "6px 12px",
                borderRadius: "6px",
                border: "none",
                cursor: "pointer",
                background: filter === f ? "#00e0ff" : "#1f2937",
                color: "#000",
                fontWeight: "bold"
              }}>
              {f}
            </button>
          ))}
        </div>

        {/* ===== ALERT QUEUE ===== */}
        <div style={card}>
          <h3 style={{ color: "#00e0ff" }}>Incident Queue</h3>
          {visibleAlerts.map((a, i) => (
            <div key={i}
              onClick={() => setSelectedAlert(a)}
              style={{
                padding: "10px",
                marginBottom: "8px",
                background: "#020617",
                borderLeft: `6px solid ${sevColor(a.severity)}`,
                cursor: "pointer"
              }}>
              <strong style={{ color: sevColor(a.severity) }}>
                [{a.severity}]
              </strong>{" "}
              {a.description}
              <div style={{ fontSize: "12px", color: "#9ca3af" }}>
                {a.timestamp} | {a.source} | {status[a.alert_id] || "OPEN"}
              </div>
            </div>
          ))}
        </div>

        {/* ===== INCIDENT DETAILS ===== */}
        {selectedAlert && (
          <div style={card}>
            <h3 style={{ color: "#facc15" }}>Incident Investigation</h3>
            <p><b>Description:</b> {selectedAlert.description}</p>
            <p><b>Source:</b> {selectedAlert.source}</p>
            <p><b>Severity:</b> {selectedAlert.severity}</p>

            <label>Status:</label>
            <select
              value={status[selectedAlert.alert_id] || "OPEN"}
              onChange={e => setStatus({ ...status, [selectedAlert.alert_id]: e.target.value })}
            >
              <option>OPEN</option>
              <option>ACKNOWLEDGED</option>
              <option>CLOSED</option>
            </select>

            <textarea
              placeholder="Analyst investigation notes..."
              value={notes[selectedAlert.alert_id] || ""}
              onChange={e => setNotes({ ...notes, [selectedAlert.alert_id]: e.target.value })}
              style={{ width: "100%", marginTop: "10px", background: "#020617", color: "#fff" }}
            />
          </div>
        )}

        {/* ===== FORENSIC TIMELINE ===== */}
        <div style={card}>
          <h3 style={{ color: "#00e0ff" }}>Forensic Timeline Reconstruction</h3>
          {timeline.map((t, i) => (
            <div key={i} style={{ fontSize: "13px", marginBottom: "4px" }}>
              {t.timestamp} — {t.description}
            </div>
          ))}
        </div>

      </div>

      <footer style={{ textAlign: "center", fontSize: "12px", color: "#6b7280", padding: "10px" }}>
        SOC Console • Startup Deployment Ready
      </footer>
    </div>
  );
}

export default App;
