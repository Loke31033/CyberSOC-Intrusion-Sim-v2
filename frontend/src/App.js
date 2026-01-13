import React, { useState, useEffect, useCallback } from 'react';
import { ShieldAlert, Clock, Activity, History, CheckCircle, Search, X, FileText, User } from 'lucide-react';

const App = () => {
  const [alerts, setAlerts] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [health, setHealth] = useState({});
  const [timeline, setTimeline] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  // 1. DATA REFRESH LOGIC (Syncs with app.py)
  const fetchAllData = useCallback(async () => {
    try {
      const [aRes, mRes, hRes] = await Promise.all([
        fetch('http://127.0.0.1:5000/api/alerts').then(res => res.json()),
        fetch('http://127.0.0.1:5000/api/soc/metrics').then(res => res.json()),
        fetch('http://127.0.0.1:5000/api/system_health').then(res => res.json())
      ]);
      setAlerts(aRes);
      setMetrics(mRes);
      setHealth(hRes);
    } catch (err) {
      console.error("Backend offline or connection refused.");
    }
  }, []);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 5000); 
    return () => clearInterval(interval);
  }, [fetchAllData]);

  // 2. INCIDENT LIFECYCLE MANAGEMENT (FSM)
  const handleStateChange = async (id, nextState) => {
    await fetch(`http://127.0.0.1:5000/api/alerts/${id}/state`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: nextState, analyst: "Analyst-01" })
    });
    fetchAllData(); // Refresh UI immediately after update
  };

  // 3. FORENSIC TIMELINE RECONSTRUCTION
  const openForensics = async (incident) => {
    setSelectedIncident(incident);
    try {
      const res = await fetch('http://127.0.0.1:5000/api/timeline');
      const data = await res.json();
      // Filter the timeline to show actions related to this specific Incident ID
      const filtered = data.filter(e => e.id === incident.id);
      setTimeline(filtered);
    } catch (err) {
      console.error("Forensic Retrieval Error");
    }
  };

  return (
    <div className="min-h-screen bg-black text-slate-100 p-6 font-mono">
      {/* HEADER: SOC ANALYTICS */}
      <header className="flex justify-between items-end mb-8 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2 uppercase">
            <ShieldAlert className="text-red-600 animate-pulse" /> SOC Command Center
          </h1>
          <p className="text-[10px] text-slate-500 tracking-widest uppercase">
            Platform Health: <span className="text-green-500">{health.status}</span> | OS: {health.os} | Uptime: {health.uptime_hours}h
          </p>
        </div>
        <div className="flex gap-3">
           <StatusPill title="Total Incidents" value={metrics.total_alerts} icon={Activity} color="text-cyan-400" />
           <StatusPill title="SLA Breach Rate" value={`${metrics.sla_breach_rate_percent}%`} icon={Clock} color="text-red-500" />
           <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5 rounded border border-slate-700">
              <User size={14} className="text-cyan-400" />
              <span className="text-[10px] font-bold uppercase text-slate-300">Analyst-01</span>
           </div>
        </div>
      </header>

      {/* INCIDENT QUEUE */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
        <div className="bg-slate-800/40 p-3 border-b border-slate-800 flex justify-between items-center">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 px-2 border-l-2 border-red-600">Active Incident Feed</span>
            <div className="flex items-center gap-2 bg-black/40 px-3 py-1 rounded">
                <Search size={14} className="text-slate-500" />
                <input 
                    className="bg-transparent border-none text-[10px] focus:outline-none text-white w-40" 
                    placeholder="Search incidents..."
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>
        </div>
        
        <table className="w-full text-left text-[11px]">
          <thead className="text-slate-500 border-b border-slate-800 bg-black/20 uppercase">
            <tr>
              <th className="p-4">Incident ID</th>
              <th className="p-4">Severity</th>
              <th className="p-4">SLA Countdown</th>
              <th className="p-4">Status</th>
              <th className="p-4 text-center">Investigation</th>
              <th className="p-4 text-center">Lifecycle Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {alerts
              .filter(a => a.desc?.toLowerCase().includes(searchQuery.toLowerCase()) || a.id.includes(searchQuery))
              .map(alert => (
              <tr key={alert.id} className="hover:bg-slate-800/40 transition-colors">
                <td className="p-4 font-bold text-cyan-500">{alert.id}</td>
                <td className="p-4">
                  <span className={`px-2 py-0.5 rounded-sm font-bold ${alert.severity === 'HIGH' ? 'bg-red-900/30 text-red-500' : 'bg-yellow-900/30 text-yellow-500'}`}>
                    {alert.severity}
                  </span>
                </td>
                <td className={`p-4 font-mono font-bold ${alert.sla === 'BREACHED' ? 'text-red-500 animate-pulse' : 'text-emerald-400'}`}>
                  {alert.sla}
                </td>
                <td className="p-4 italic text-slate-500 uppercase">{alert.status}</td>
                <td className="p-4 text-center">
                  <button onClick={() => openForensics(alert)} className="text-cyan-400 hover:text-white flex items-center gap-1 mx-auto transition">
                    <History size={14} /> Reconstruct Timeline
                  </button>
                </td>
                <td className="p-4 text-center">
                  {alert.status === 'OPEN' && (
                    <button onClick={() => handleStateChange(alert.id, 'ACKNOWLEDGED')} className="bg-cyan-700 hover:bg-cyan-600 px-4 py-1 rounded text-white font-bold transition w-32 shadow-lg">ACKNOWLEDGE</button>
                  )}
                  {alert.status === 'ACKNOWLEDGED' && (
                    <button onClick={() => handleStateChange(alert.id, 'CLOSED')} className="bg-emerald-700 hover:bg-emerald-600 px-4 py-1 rounded text-white font-bold transition w-32 shadow-lg">RESOLVE</button>
                  )}
                  {alert.status === 'CLOSED' && (
                    <div className="flex items-center justify-center gap-1 text-slate-600">
                         <CheckCircle size={14} /> INCIDENT CLOSED
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* FORENSIC SIDE PANEL (TIMELINE RECONSTRUCTION) */}
      {selectedIncident && (
        <div className="fixed inset-y-0 right-0 w-[420px] bg-slate-900 border-l border-slate-700 shadow-2xl p-6 z-50 animate-in slide-in-from-right overflow-y-auto">
          <div className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
            <h2 className="text-sm font-bold flex items-center gap-2 uppercase">
                <FileText className="text-cyan-400" /> Evidence Logs: {selectedIncident.id}
            </h2>
            <button onClick={() => setSelectedIncident(null)} className="text-slate-500 hover:text-white"><X size={20}/></button>
          </div>

          <div className="bg-black/40 p-4 rounded border border-slate-800 mb-8">
             <div className="text-[9px] text-slate-500 uppercase font-bold mb-1">Source Analysis</div>
             <p className="text-xs text-slate-200 italic">"{selectedIncident.desc}"</p>
          </div>

          <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-6 flex items-center gap-2">
            <History size={14} /> Action Trace (Audit Trail)
          </h3>
          
          <div className="space-y-6 relative before:absolute before:inset-0 before:ml-2 before:w-0.5 before:bg-slate-800">
            {timeline.length > 0 ? timeline.map((event, i) => (
              <div key={i} className="relative pl-8">
                <div className="absolute left-0 top-1.5 w-4 h-4 rounded-full bg-cyan-600 border-4 border-slate-900"></div>
                <p className="text-[9px] text-slate-500 font-bold">{event.timestamp}</p>
                <p className="text-[11px] text-slate-300 leading-snug">{event.description}</p>
              </div>
            )) : (
                <div className="pl-8 text-[10px] text-slate-600 italic">No forensic history found for this ID.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const StatusPill = ({ title, value, icon: Icon, color }) => (
  <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded shadow-sm">
    <Icon size={14} className={color} />
    <div>
      <div className="text-[7px] text-slate-500 uppercase font-bold leading-none mb-0.5">{title}</div>
      <div className="text-[12px] font-black leading-none">{value}</div>
    </div>
  </div>
);

export default App;
