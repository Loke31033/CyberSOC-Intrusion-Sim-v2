from flask import Flask, jsonify, request
from flask_cors import CORS
import os, threading, time, sqlite3
from datetime import datetime, timedelta
from db import init_db, get_db

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
TIMELINE_PATH = os.path.join(ROOT_DIR, 'reports', 'timeline.csv')
SLA_POLICY = {"HIGH": 15, "MEDIUM": 60, "LOW": 240}

# --- HELPER: FLEXIBLE DATE PARSING ---
def parse_date(date_str):
    try:
        return datetime.strptime(date_str.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
    except:
        return datetime.now()

# --- NEW: TIMELINE API ---
@app.route("/api/timeline", methods=["GET"])
def get_timeline():
    """Practically solves the 'Evidence Reconstruction' problem for analysts."""
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
        return jsonify(events[::-1]) # Return newest first
    except Exception as e:
        return jsonify([{"timestamp": str(datetime.now()), "description": f"Error reading logs: {e}"}])

# --- REMAINING SOC ROUTES ---

@app.route("/api/alerts", methods=["GET"])
def fetch_alerts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT alert_id, source, severity, description, status, timestamp FROM alerts ORDER BY timestamp DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonify([{
        "id": r[0], "source": r[1], "severity": r[2], "desc": r[3], 
        "status": r[4], "time": r[5],
        "sla": "15m" 
    } for r in rows])

@app.route("/api/soc/metrics")
def soc_metrics():
    return jsonify({"total_alerts": 197, "mttr_days": 0.5, "sla_breach_rate_percent": 2})

@app.route("/api/system_health")
def system_health():
    return jsonify({"os": "Kali Linux", "uptime_hours": 24.5, "status": "Healthy"})

@app.route("/api/alerts/<id>/state", methods=["POST"])
def update_state(id):
    next_state = request.json.get("state")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE alerts SET status=? WHERE alert_id=?", (next_state, id))
    
    # LOG ACTION TO TIMELINE
    with open(TIMELINE_PATH, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, {id}, Analyst transitioned state to {next_state}\n")
        
    conn.commit()
    conn.close()
    return jsonify({"success": True})

if __name__ == "__main__":
    init_db()
    print(f"🔥 SOC Backend with Timeline API: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
