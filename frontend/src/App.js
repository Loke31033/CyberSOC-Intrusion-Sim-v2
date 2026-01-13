import React, { useState, useEffect, useCallback } from 'react';
import { ShieldAlert, Clock, Activity, History, CheckCircle, Search, X, FileText, User, Terminal, Send } from 'lucide-react';

const App = () => {
  const [alerts, setAlerts] = useState([]);
  const [metrics, setMetrics] = useState({ total_alerts: 0, mttr_days: 0, sla_breach_rate_percent: 0 });
  const [health, setHealth] = useState({ status: "Connecting...", os: "...", uptime_hours: 0 });
  const [timeline, setTimeline] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Investigation notes state
  const [noteInput, setNoteInput] = useState("");

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
      console.error("SOC Backend Unreachable");
    }
  }, []);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 5000); 
    return () => clearInterval(interval);
  }, [fetchAllData]);

  const handleStateChange = async (id, nextState) => {
    try {
      await fetch(`http://127.0.0.1:5000/api/alerts/${id}/state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: nextState })
      });
      fetchAllData();
    } catch (err) {
      alert("Status Update Failed");
    }
  };

  const submitNote = async () => {
    if (!noteInput.trim()) return;
    try {
      await fetch(`http://127.0.0.1:5000/api/alerts/${selectedIncident.id}/state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            state: selectedIncident.status, 
            analyst: "ANALYST_01", 
            note: noteInput 
        })
      });
      setNoteInput(""); 
      // Refresh timeline to show the new note
      const res = await fetch('http://127.0.0.1:5000/api/timeline');
      const data = await res.json();
      setTimeline(data.filter(e => e.id === selectedIncident.id));
    } catch (err) {
      console.error("Failed to save note");
    }
  };

  const openForensics = async (incident) => {
    setSelectedIncident(incident);
    try {
      const res = await fetch('http://127.0.0.1:5000/api/timeline');
      const data = await res.json();
      setTimeline(data.filter(e => e.id === incident.id));
    } catch (err) {
      setTimeline([]);
    }
  };

  return (
    <div className="min-h-screen bg-black text-slate-100 p-6 font-mono selection:bg-cyan-500/30">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-black text-white flex items-center gap-3 tracking-tighter">
            <ShieldAlert className="text-red-600 animate-pulse" size={32} /> 
            CYBER-SOC <span className="text-red-600">v2.0</span>
          </h1>
          <div className="flex gap-4 mt-2">
            <p className="text-[10px] text-slate-500 uppercase tracking-widest flex items-center gap-1">
              <Activity size={12} className="text-green-500"/> System: {health.os}
            </p>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest flex items-center gap-1">
              <Clock size={12} className="text-cyan-500"/> Uptime: {health.uptime_hours}h
            </p>
          </div>
        </div>
        
        <div className="flex gap-4">
           <StatusPill title="Incidents" value={metrics.total_alerts} color="text-cyan-400" />
           <StatusPill title="SLA Breach" value={`${metrics.sla_breach_rate_percent}%`} color="text-red-500" />
           <div className="bg-slate-900 border border-slate-700 px-4 py-2 rounded-lg flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-cyan-950 flex items-center justify-center border border-cyan-500/50">
                <User size={16} className="text-cyan-400" />
              </div>
              <span className="text-xs font-bold text-slate-300">ANALYST_01</span>
           </div>
        </div>
      </header>

      {/* THREAT SEVERITY BAR */}
      <div className="mb-6 grid grid-cols-3 gap-1 h-1.5 rounded-full overflow-hidden bg-slate-800">
          <div style={{width: '70%'}} className="bg-red-600"></div>
          <div style={{width: '20%'}} className="bg-yellow-500"></div>
          <div style={{width: '10%'}} className="bg-emerald-500"></div>
      </div>

      {/* LIVE INTRUSION FEED TABLE */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-md shadow-2xl">
        <div className="bg-slate-800/40 p-4 border-b border-slate-800 flex justify-between items-center">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
              <Terminal size={16} className="text-red-600"/> Live Intrusion Feed
            </h2>
            <div className="flex items-center gap-2 bg-black/60 px-4 py-2 rounded-md border border-slate-700">
                <Search size={14} className="text-slate-500" />
                <input 
                    className="bg-transparent border-none text-xs focus:outline-none text-white w-64" 
                    placeholder="Search by IP, ID, or Attack Type..."
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>
        </div>
        
        <table className="w-full text-left text-xs">
          <thead className="text-slate-500 border-b border-slate-800 bg-black/40 uppercase font-bold">
            <tr>
              <th className="p-5">Incident ID</th>
              <th className="p-5">Severity</th>
              <th className="p-5">SLA Countdown</th>
              <th className="p-5">Status</th>
              <th className="p-5 text-center">Investigation</th>
              <th className="p-5 text-center">Lifecycle Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {alerts
              .filter(a => (a.desc?.toLowerCase() || "").includes(searchQuery.toLowerCase()) || a.id.includes(searchQuery))
              .map(alert => (
              <tr key={alert.id} className="hover:bg-cyan-500/5 transition-all group">
                <td className="p-5 font-bold text-cyan-500 group-hover:text-cyan-400">{alert.id}</td>
                <td className="p-5">
                  <span className={`px-3 py-1 rounded text-[10px] font-black ${
                    alert.severity === 'HIGH' ? 'bg-red-500/20 text-red-500 border border-red-500/30' : 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/30'
                  }`}>
                    {alert.severity}
                  </span>
                </td>
                <td className={`p-5 font-mono font-bold ${alert.sla_color === 'red' ? 'text-red-500 animate-pulse' : 'text-emerald-400'}`}>
                  {alert.sla_remaining}
                </td>
                <td className="p-5">
                    <div className="flex items-center gap-2">
                       <div className={`w-1.5 h-1.5 rounded-full ${alert.status === 'OPEN' ? 'bg-red-500' : alert.status === 'CLOSED' ? 'bg-slate-600' : 'bg-cyan-500'}`}></div>
                       <span className="text-slate-400 font-medium uppercase text-[10px]">{alert.status}</span>
                    </div>
                </td>
                <td className="p-5 text-center">
                  <button onClick={() => openForensics(alert)} className="bg-slate-800 hover:bg-slate-700 text-cyan-400 px-3 py-1.5 rounded-md flex items-center gap-2 mx-auto transition-all border border-slate-700">
                    <History size={14} /> Reconstruct
                  </button>
                </td>
                <td className="p-5 text-center">
                  {alert.status === 'OPEN' && (
                    <button onClick={() => handleStateChange(alert.id, 'ACKNOWLEDGED')} className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-1.5 rounded-md font-bold transition shadow-lg shadow-cyan-900/20 w-40">ACKNOWLEDGE</button>
                  )}
                  {alert.status === 'ACKNOWLEDGED' && (
                    <button onClick={() => handleStateChange(alert.id, 'CLOSED')} className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-1.5 rounded-md font-bold transition w-40">RESOLVE CASE</button>
                  )}
                  {alert.status === 'CLOSED' && (
                    <div className="text-slate-600 flex items-center justify-center gap-2 font-bold uppercase tracking-widest text-[10px]">
                       <CheckCircle size={14} /> Archived
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ENHANCED FORENSIC PANEL */}
      {selectedIncident && (
        <div className="fixed inset-y-0 right-0 w-[450px] bg-slate-900 border-l border-slate-700 shadow-[-20px_0_50px_rgba(0,0,0,0.5)] p-8 z-50 animate-in slide-in-from-right overflow-y-auto">
          <div className="flex justify-between items-center mb-8 border-b border-slate-800 pb-5">
            <div>
              <h2 className="text-lg font-black text-white uppercase tracking-tighter flex items-center gap-2">
                <FileText className="text-cyan-400" size={20} /> Forensic Audit
              </h2>
              <p className="text-[10px] text-cyan-500 font-bold tracking-widest">{selectedIncident.id}</p>
            </div>
            <button onClick={() => setSelectedIncident(null)} className="text-slate-500 hover:text-white transition-colors p-2 hover:bg-slate-800 rounded-full"><X size={24}/></button>
          </div>

          {/* 1. Investigation Notes Input Area */}
          <div className="mb-8">
            <h3 className="text-[10px] font-black text-slate-500 uppercase mb-3 flex items-center gap-2 tracking-[0.2em]">
              <Terminal size={14} className="text-cyan-500"/> Investigation Notes
            </h3>
            <div className="relative group">
              <textarea 
                value={noteInput}
                onChange={(e) => setNoteInput(e.target.value)}
                placeholder="Enter findings, evidence URLs, or analyst remarks..."
                className="w-full bg-black/40 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50 transition-all min-h-[100px] resize-none"
              />
              <button 
                onClick={submitNote}
                className="absolute bottom-3 right-3 p-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md transition-all disabled:opacity-50"
                disabled={!noteInput.trim()}
              >
                <Send size={14} />
              </button>
            </div>
          </div>

          {/* 2. Download Report Button */}
          <div className="mb-8">
            <button 
              onClick={() => window.open(`http://127.0.0.1:5000/api/alerts/${selectedIncident.id}/report/download`)}
              className="w-full group flex items-center justify-between bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 p-4 rounded-xl transition-all duration-300"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-950 rounded-lg border border-cyan-500/30 group-hover:bg-cyan-500 group-hover:text-black transition-all">
                  <FileText size={18} className="text-cyan-400 group-hover:text-black" />
                </div>
                <div className="text-left">
                  <div className="text-[10px] font-black text-cyan-400 uppercase tracking-widest">Case Finalization</div>
                  <div className="text-[9px] text-slate-400 font-bold uppercase tracking-tighter">Generate Official Report</div>
                </div>
              </div>
              <History size={16} className="text-cyan-600 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          {/* 3. Threat Vector Card */}
          <div className="bg-black/60 p-5 rounded-lg border border-slate-800 mb-8">
             <div className="text-[9px] text-slate-500 uppercase font-black mb-2 flex items-center gap-2">
               <ShieldAlert size={12} className="text-red-500"/> Threat Vector
             </div>
             <p className="text-xs text-slate-200 leading-relaxed font-sans font-medium">
               "{selectedIncident.desc}"
             </p>
          </div>

          {/* 4. Sequence Reconstruction Timeline */}
          <h3 className="text-[10px] font-black text-slate-500 uppercase mb-6 flex items-center gap-2 tracking-[0.2em]">
            <History size={14} className="text-cyan-500"/> Sequence Reconstruction
          </h3>
          
          <div className="space-y-8 relative before:absolute before:inset-0 before:ml-[7px] before:w-0.5 before:bg-slate-800">
            {timeline.length > 0 ? timeline.map((event, i) => (
              <div key={i} className="relative pl-10 group">
                <div className="absolute left-0 top-1 w-[15px] h-[15px] rounded-full bg-slate-900 border-2 border-cyan-500 group-hover:scale-125 transition-transform z-10 shadow-[0_0_10px_rgba(6,182,212,0.5)]"></div>
                <p className="text-[9px] text-cyan-500 font-black mb-1">{event.timestamp}</p>
                <p className="text-xs text-slate-300 font-medium leading-snug">{event.description}</p>
              </div>
            )) : (
              <div className="pl-10 text-[10px] text-slate-600 italic">Analyzing logs for historical patterns...</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const StatusPill = ({ title, value, color }) => (
  <div className="bg-slate-900/50 border border-slate-800 px-5 py-2 rounded-xl shadow-lg flex flex-col items-center min-w-[100px]">
    <span className="text-[8px] text-slate-500 uppercase font-black tracking-widest mb-1">{title}</span>
    <span className={`text-xl font-black ${color}`}>{value}</span>
  </div>
);

export default App;
