from flask import Flask, jsonify, request
from flask_cors import CORS
import os, threading, time, sqlite3, subprocess
from datetime import datetime, timedelta
from db import init_db, get_db
from flask import send_file
import io
app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
REPORTS_DIR = os.path.join(ROOT_DIR, 'reports')
TIMELINE_PATH = os.path.join(REPORTS_DIR, 'timeline.csv')
SLA_POLICY = {"HIGH": 15, "MEDIUM": 60, "LOW": 240}

os.makedirs(REPORTS_DIR, exist_ok=True)

# --- HELPER: SLA CALCULATION ---
def calculate_sla_remaining(start_time_str, severity):
    try:
        clean_ts = start_time_str.replace('T', ' ')
        start_dt = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
        limit = SLA_POLICY.get(severity, 60)
        deadline = start_dt + timedelta(minutes=limit)
        diff = deadline - datetime.now()
        seconds = int(diff.total_seconds())
        if seconds < 0:
            return "EXPIRED", "red"
        return f"{seconds // 60}m {seconds % 60}s", "green"
    except:
        return "N/A", "gray"

# --- API: FORENSIC TIMELINE RECONSTRUCTION ---
@app.route("/api/timeline", methods=["GET"])
def get_timeline():
    if not os.path.exists(TIMELINE_PATH):
        return jsonify([])
    events = []
    try:
        with open(TIMELINE_PATH, 'r') as f:
            for line in f.readlines():
                parts = line.strip().split(',', 2)
                if len(parts) >= 3:
                    events.append({
                        "timestamp": parts[0],
                        "id": parts[1].strip(),
                        "description": parts[2].strip()
                    })
        return jsonify(events[::-1])
    except Exception as e:
        return jsonify([{"timestamp": str(datetime.now()), "description": f"Log Error: {e}"}])

# --- API: ALERT MANAGEMENT ---
@app.route("/api/alerts", methods=["GET"])
def fetch_alerts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT alert_id, source, severity, description, status, timestamp FROM alerts ORDER BY timestamp DESC")
    rows = cur.fetchall()
    conn.close()
    results = []
    for r in rows:
        sla_val, sla_col = calculate_sla_remaining(r[5], r[2])
        results.append({
            "id": r[0], "source": r[1], "severity": r[2],
            "desc": r[3], "status": r[4], "time": r[5],
            "sla_remaining": sla_val, "sla_color": sla_col
        })
    return jsonify(results)



@app.route("/api/alerts/<id>/report/download", methods=["GET"])
def download_report(id):
    """Generates a clean, professional forensic report for the analyst."""
    report_content = f"""
============================================================
           CYBER-SOC V2.0 OFFICIAL INCIDENT REPORT          
============================================================
INCIDENT ID: {id}
REPORT DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ANALYST: ANALYST_01
============================================================

1. FORENSIC TIMELINE & AUDIT TRAIL
------------------------------------------------------------
"""
    found = False
    if os.path.exists(TIMELINE_PATH):
        with open(TIMELINE_PATH, 'r') as f:
            for line in f.readlines():
                if id in line:
                    # Clean up the line for the report
                    report_content += f"[*] {line.strip()}\n"
                    found = True
    
    if not found:
        report_content += "[!] No forensic events recorded for this ID.\n"

    report_content += f"""
------------------------------------------------------------
2. SYSTEM CLASSIFICATION
------------------------------------------------------------
REPORT STATUS: VERIFIED
DATA SOURCE: {TIMELINE_PATH}
============================================================
                   END OF OFFICIAL RECORD                   
============================================================
"""
    
    # Create the file in memory
    mem = io.BytesIO()
    mem.write(report_content.encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        as_attachment=True,
        download_name=f"SOC_Report_{id}.txt",
        mimetype='text/plain'
    )

@app.route("/api/alerts/<id>/state", methods=["POST"])
def update_state(id):
    """Handles Incident Lifecycle transitions and Investigation Notes."""
    data = request.json
    next_state = data.get("state")
    note = data.get("note") # Carefully added to catch the note from frontend
    
    conn = get_db()
    cur = conn.cursor()
    
    # Update status only if state is provided
    if next_state:
        cur.execute("UPDATE alerts SET status=? WHERE alert_id=?", (next_state, id))
    
    # PERMANENT FORENSIC RECORD
    with open(TIMELINE_PATH, 'a') as f:
        log_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if note:
            # Added logic to write the investigation note to your CSV
            f.write(f"{log_time}, {id}, INVESTIGATION NOTE: {note}\n")
        elif next_state:
            f.write(f"{log_time}, {id}, Analyst transitioned state to {next_state}\n")
        
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# --- SOC ANALYTICS ---
@app.route("/api/soc/metrics")
def soc_metrics():
    return jsonify({"total_alerts": 197, "mttr_days": 0.5, "sla_breach_rate_percent": 2})

@app.route("/api/system_health")
def system_health():
    return jsonify({"os": "Kali Linux", "uptime_hours": 24.5, "status": "Healthy"})

# --- AUTO-ESCALATION ENGINE ---
def auto_escalate_worker():
    while True:
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT alert_id, severity, timestamp FROM alerts WHERE status != 'CLOSED'")
            for aid, sev, ts in cur.fetchall():
                limit = SLA_POLICY.get(sev, 60)
                deadline = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=limit)
                if datetime.now() > deadline and sev != "HIGH":
                    cur.execute("UPDATE alerts SET severity='HIGH' WHERE alert_id=?", (aid,))
                    with open(TIMELINE_PATH, 'a') as f:
                        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, {aid}, SYSTEM: SLA Breached - Auto-Escalated to HIGH\n")
            conn.commit()
            conn.close()
        except: pass
        time.sleep(30)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=auto_escalate_worker, daemon=True).start()
    correlate_script = os.path.join(ROOT_DIR, 'scripts', 'correlate.py')
    if os.path.exists(correlate_script):
        subprocess.run(["python3", correlate_script])
    app.run(debug=True, port=5000)
