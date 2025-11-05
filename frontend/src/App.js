// src/App.js
import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function App() {
  const [iocs, setIocs] = useState({});
  const [findings, setFindings] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [sensorFindings, setSensorFindings] = useState([]);
  const [sensorStats, setSensorStats] = useState({ temp: [], vib: [], motion: [] });
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [logsCount, setLogsCount] = useState(0);
  const timelineEndRef = useRef(null);

  const scrollToBottom = () => {
    if (timelineEndRef.current) {
      timelineEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [timeline]);

  const fetchInitialData = async () => {
    try {
      const [iocsRes, findingsRes, sensorRes] = await Promise.all([
        axios.get("http://127.0.0.1:5000/api/iocs"),
        axios.get("http://127.0.0.1:5000/api/findings"),
        axios.get("http://127.0.0.1:5000/api/sensors"),
      ]);
      setIocs(iocsRes.data);
      setFindings(findingsRes.data);
      setSensorFindings(sensorRes.data.sensor_findings || []);
      setSensorStats(sensorRes.data.sensor_stats || { temp: [], vib: [], motion: [] });
    } catch (err) {
      console.error("Error fetching IOCs/Findings/Sensors:", err);
    }
  };

  const fetchTimeline = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/api/timeline");
      setTimeline(res.data);
      setLogsCount(res.data.length);
    } catch (err) {
      console.error("Error fetching timeline:", err);
    }
  };

  useEffect(() => {
    fetchInitialData();
    fetchTimeline();

    // 🔁 Auto-refresh Smart Sensor section every 10s
    const interval = setInterval(async () => {
      try {
        const res = await axios.get("http://127.0.0.1:5000/api/sensors");
        setSensorFindings(res.data.sensor_findings || []);
        setSensorStats(res.data.sensor_stats || { temp: [], vib: [], motion: [] });
      } catch {}
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const formatDatetime = (dt, isEnd = false) => {
    if (!dt) return "";
    return dt.length === 16 ? dt + (isEnd ? ":59" : ":00") : dt;
  };

  const searchTimeline = async () => {
    if (!startDate || !endDate) {
      alert("Please select both start and end date/time.");
      return;
    }
    try {
      const res = await axios.get("http://127.0.0.1:5000/api/timeline", {
        params: {
          start: formatDatetime(startDate),
          end: formatDatetime(endDate, true),
        },
      });
      setTimeline(res.data);
      setLogsCount(res.data.length);
    } catch (err) {
      console.error("Error filtering timeline:", err);
    }
  };

  const resetTimeline = () => {
    setStartDate("");
    setEndDate("");
    fetchTimeline();
  };

  const downloadReport = async (format) => {
    const url =
      format === "json"
        ? "http://127.0.0.1:5000/api/download/json"
        : "http://127.0.0.1:5000/api/download/csv";

    try {
      const res = await axios.get(url, { responseType: "blob" });
      const href = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = href;
      link.setAttribute("download", `report.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Error downloading report:", err);
    }
  };

  const styles = {
    page: {
      backgroundColor: "#0a0f1c",
      color: "#e0e6ed",
      minHeight: "100vh",
      padding: "25px",
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    },
    card: {
      background: "#141b2d",
      borderRadius: "12px",
      padding: "18px",
      marginBottom: "25px",
      boxShadow: "0 0 18px rgba(0,255,255,0.15)",
      transition: "transform 0.2s ease, box-shadow 0.2s ease",
    },
    heading: {
      color: "#00e0ff",
      borderBottom: "2px solid #00e0ff",
      paddingBottom: "6px",
      marginBottom: "12px",
    },
    button: {
      background: "linear-gradient(90deg, #007bff, #00d4ff)",
      border: "none",
      color: "white",
      padding: "8px 14px",
      borderRadius: "6px",
      cursor: "pointer",
      fontWeight: "bold",
      boxShadow: "0 0 10px rgba(0,212,255,0.3)",
    },
  };

  // Chart.js live data from Smart Sensors
  const chartData = {
    labels: sensorStats.temp.map((_, i) => i + 1),
    datasets: [
      {
        label: "🌡️ Temperature (°C)",
        data: sensorStats.temp,
        borderColor: "#00e0ff",
        fill: false,
        tension: 0.4,
      },
      {
        label: "💥 Vibration",
        data: sensorStats.vib,
        borderColor: "#ff6b6b",
        fill: false,
        tension: 0.4,
      },
      {
        label: "🌀 Motion Level",
        data: sensorStats.motion,
        borderColor: "#22c55e",
        fill: false,
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        labels: {
          color: "#fff"
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: "#ccc"
        },
        grid: {
          color: "rgba(255,255,255,0.1)"
        }
      },
      y: {
        ticks: {
          color: "#ccc"
        },
        grid: {
          color: "rgba(255,255,255,0.1)"
        }
      }
    }
  };

  return (
    <div style={styles.page}>
      <h1 style={{ color: "#00e0ff", textAlign: "center", marginBottom: "30px" }}>
        🛰️ CyberSOC Intrusion + Smart Sensor Dashboard
      </h1>

      {/* 🔹 Stat Summary Cards */}
      <div style={{ display: "flex", gap: "20px", flexWrap: "wrap", justifyContent: "center" }}>
        <div style={{ ...styles.card, width: "200px", textAlign: "center" }}>
          <h2 style={{ color: "#00e0ff" }}>{logsCount}</h2>
          <p>Total Logs</p>
        </div>
        <div style={{ ...styles.card, width: "200px", textAlign: "center" }}>
          <h2 style={{ color: "#ff6b6b" }}>{findings.length}</h2>
          <p>Active Alerts</p>
        </div>
        <div style={{ ...styles.card, width: "200px", textAlign: "center" }}>
          <h2 style={{ color: "#22c55e" }}>{Object.keys(iocs).length}</h2>
          <p>IOCs Detected</p>
        </div>
      </div>

      {/* 🔹 IOCs */}
      <div style={styles.card}>
        <h3 style={styles.heading}>📌 Indicators of Compromise (IOCs)</h3>
        <pre
          style={{
            background: "#0b1220",
            padding: "10px",
            borderRadius: "8px",
            overflowX: "auto",
          }}
        >
          {JSON.stringify(iocs, null, 2)}
        </pre>
      </div>

      {/* 🔹 Findings */}
      <div style={styles.card}>
        <h3 style={styles.heading}>🚨 Security Findings</h3>
        <ul>
          {findings.length > 0 ? (
            findings.map((f, i) => (
              <li key={i} style={{ color: "#ff6b6b", marginBottom: "4px" }}>
                ⚠️ {f}
              </li>
            ))
          ) : (
            <p style={{ color: "#6c757d" }}>✅ No major alerts detected</p>
          )}
        </ul>
      </div>

      {/* 🔹 Timeline */}
      <div style={styles.card}>
        <h3 style={styles.heading}>📅 Event Timeline</h3>
        <div style={{ display: "flex", gap: "10px", marginBottom: "10px", flexWrap: "wrap" }}>
          <label>Start:</label>
          <input
            type="datetime-local"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={{
              background: "#0b1220",
              color: "#fff",
              border: "1px solid #00e0ff",
              borderRadius: "6px",
              padding: "4px",
            }}
          />
          <label>End:</label>
          <input
            type="datetime-local"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={{
              background: "#0b1220",
              color: "#fff",
              border: "1px solid #00e0ff",
              borderRadius: "6px",
              padding: "4px",
            }}
          />
          <button onClick={searchTimeline} style={styles.button}>
            🔍 Search
          </button>
          <button
            onClick={resetTimeline}
            style={{
              ...styles.button,
              background: "linear-gradient(90deg,#6c757d,#495057)",
            }}
          >
            🔄 Reset
          </button>
        </div>

        <div style={{ overflowX: "auto", maxHeight: "400px", overflowY: "auto" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              backgroundColor: "#111827",
              color: "#e0e6ed",
            }}
          >
            <thead>
              <tr>
                <th
                  style={{
                    background: "#1f2937",
                    position: "sticky",
                    top: 0,
                    textAlign: "left",
                    padding: "10px",
                    borderBottom: "2px solid #00e0ff",
                  }}
                >
                  Timestamp
                </th>
                <th
                  style={{
                    background: "#1f2937",
                    position: "sticky",
                    top: 0,
                    textAlign: "left",
                    padding: "10px",
                    borderBottom: "2px solid #00e0ff",
                  }}
                >
                  Description
                </th>
              </tr>
            </thead>
            <tbody>
              {timeline.length > 0 ? (
                timeline.map((t, i) => (
                  <tr key={i}>
                    <td style={{ padding: "8px", borderBottom: "1px solid #2d3748" }}>
                      {t.timestamp}
                    </td>
                    <td style={{ padding: "8px", borderBottom: "1px solid #2d3748" }}>
                      {t.description}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="2" style={{ textAlign: "center", color: "#aaa" }}>
                    No data available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          <div ref={timelineEndRef}></div>
        </div>
      </div>

      {/* 🔹 Smart Sensor Section */}
      <div style={styles.card}>
        <h3 style={styles.heading}>🌡️ Smart Sensor System (Live IoT Monitoring)</h3>
        <p style={{ color: "#aaa", fontSize: "14px" }}>Auto-refreshing every 10 seconds...</p>
        {sensorFindings.length > 0 ? (
          <ul
            style={{
              background: "#fff3cd1a",
              padding: "10px",
              borderRadius: "8px",
              listStyleType: "none",
            }}
          >
            {sensorFindings.map((alert, i) => (
              <li key={i} style={{ color: "#ffd166", marginBottom: "6px" }}>
                ⚠️ {alert}
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ color: "#6ee7b7" }}>✅ No anomalies detected</p>
        )}

        {/* 🔹 Real-time Graph */}
        <div style={{ marginTop: "20px" }}>
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>

      {/* 🔹 Download Buttons */}
      <div style={{ display: "flex", gap: "10px", justifyContent: "center" }}>
        <button
          onClick={() => downloadReport("json")}
          style={{
            ...styles.button,
            background: "linear-gradient(90deg,#28a745,#00d4ff)",
          }}
        >
          ⬇️ Download JSON
        </button>
        <button
          onClick={() => downloadReport("csv")}
          style={{
            ...styles.button,
            background: "linear-gradient(90deg,#17a2b8,#00d4ff)",
          }}
        >
          ⬇️ Download CSV
        </button>
      </div>
    </div>
  );
}

export default App;
