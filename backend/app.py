from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import os, json, threading, subprocess, psutil, platform, time, random
from datetime import datetime, timedelta
from flask import send_from_directory
from db import init_db, get_db
import sqlite3

# -------------------------------------------------
# Flask App Initialization (FIXED)
# -------------------------------------------------

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)


app = Flask(
    __name__,
    static_folder="../frontend/build/static",
    static_url_path="/static",
    template_folder="../frontend/build"
)

init_db()


# -------------------------------------------------
# ROOT
# -------------------------------------------------
#@app.route('/')
#def index():
   # return "✅ CyberSOC + Smart Sensor Flask API running"

# -------------------------------------------------
# IOC APIs
# -------------------------------------------------
@app.route('/api/iocs')
def get_iocs():
    path = os.path.join(REPORTS_DIR, 'iocs.json')
    if not os.path.exists(path):
        return jsonify({})
    with open(path) as f:
        return jsonify(json.load(f))

# -------------------------------------------------
# FINDINGS
# -------------------------------------------------
@app.route('/api/findings')
def get_findings():
    path = os.path.join(REPORTS_DIR, 'findings.txt')
    if not os.path.exists(path):
        return jsonify([])
    with open(path) as f:
        return jsonify(f.read().splitlines())

# -------------------------------------------------
# TIMELINE
# -------------------------------------------------
@app.route('/api/timeline')
def get_timeline():
    path = os.path.join(REPORTS_DIR, 'timeline.csv')
    if not os.path.exists(path):
        return jsonify([])
    timeline = []
    with open(path) as f:
        next(f, None)
        for line in f:
            parts = line.strip().split(",", 1)
            if len(parts) == 2:
                timestamp, desc = parts
                timeline.append({
                    "timestamp": timestamp,
                    "description": desc
                })
    return jsonify(timeline)

# -------------------------------------------------
# SMART SENSOR (Simulation)
# -------------------------------------------------
@app.route('/api/sensors')
def get_sensors():
    sensor_file = os.path.join(REPORTS_DIR, 'sensor_findings.txt')
    history_file = os.path.join(REPORTS_DIR, 'sensor_history.json')

    findings = []

    if os.path.exists(sensor_file):
        with open(sensor_file) as f:
            findings = [l for l in f.read().splitlines() if l.strip()]

    temp = round(random.uniform(20, 80), 2)
    vib = round(random.uniform(0, 10), 2)
    motion = random.choice([0, 1])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if temp > 70:
        findings.append(f"🔥 High temperature {temp}°C at {now}")
    if vib > 7:
        findings.append(f"⚠ High vibration {vib} at {now}")
    if motion == 1:
        findings.append(f"🚨 Motion detected at {now}")

    with open(sensor_file, "w") as f:
        for line in findings[-10:]:
            f.write(line + "\n")

    history = {"temp": [], "vib": [], "motion": []}
    if os.path.exists(history_file):
        with open(history_file) as f:
            history = json.load(f)

    history["temp"].append(temp)
    history["vib"].append(vib)
    history["motion"].append(motion)

    history["temp"] = history["temp"][-20:]
    history["vib"] = history["vib"][-20:]
    history["motion"] = history["motion"][-20:]

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    return jsonify({
        "sensor_findings": findings[-10:],
        "sensor_stats": history
    })

# -------------------------------------------------
# SYSTEM HEALTH
# -------------------------------------------------
@app.route('/api/system_health')
def system_health():
    uptime = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
    return jsonify({
        "os": platform.system(),
        "uptime_hours": round(uptime / 3600, 2),
        "cpu": psutil.cpu_percent(interval=0.5),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    })

# -------------------------------------------------
# DOWNLOADS
# -------------------------------------------------
@app.route('/api/download/json')
def download_json():
    path = os.path.join(REPORTS_DIR, 'iocs.json')
    return send_file(path, as_attachment=True)

@app.route('/api/download/csv')
def download_csv():
    path = os.path.join(REPORTS_DIR, 'timeline.csv')
    return send_file(path, as_attachment=True)

# =================================================
# ✅ PHASE-3 STEP-1: VIEW CASES
# =================================================
@app.route('/api/cases')
def get_cases():
    cases_file = os.path.join(REPORTS_DIR, 'cases.json')
    if not os.path.exists(cases_file):
        return jsonify([])
    with open(cases_file) as f:
        return jsonify(json.load(f))

@app.route('/api/cases/<incident_id>')
def get_case(incident_id):
    cases_file = os.path.join(REPORTS_DIR, 'cases.json')
    with open(cases_file) as f:
        cases = json.load(f)
    for case in cases:
        if case["incident_id"] == incident_id:
            return jsonify(case)
    return jsonify({"error": "Incident not found"}), 404

# =================================================
# ✅ PHASE-3 STEP-2: CASE LIFECYCLE
# =================================================
@app.route('/api/cases/assign', methods=['POST'])
def assign_case():
    data = request.json
    cases_file = os.path.join(REPORTS_DIR, 'cases.json')
    with open(cases_file) as f:
        cases = json.load(f)

    for c in cases:
        if c["incident_id"] == data["incident_id"]:
            c["assigned_to"] = data["analyst"]
            c["status"] = "IN-PROGRESS"


    with open(cases_file, "w") as f:
        json.dump(cases, f, indent=4)

    return jsonify({"message": "Analyst assigned"})

@app.route('/api/cases/note', methods=['POST'])
def add_note():
    data = request.json
    cases_file = os.path.join(REPORTS_DIR, 'cases.json')
    with open(cases_file) as f:
        cases = json.load(f)

    for c in cases:
        if c["incident_id"] == data["incident_id"]:
            c.setdefault("notes", [])
            c["notes"].append({
                "time": datetime.now().isoformat(),
                "note": data["note"]
            })

    with open(cases_file, "w") as f:
        json.dump(cases, f, indent=4)

    return jsonify({"message": "Note added"})

@app.route('/api/cases/close', methods=['POST'])
def close_case():
    data = request.json
    cases_file = os.path.join(REPORTS_DIR, 'cases.json')
    with open(cases_file) as f:
        cases = json.load(f)

    for c in cases:
        if c["incident_id"] == data["incident_id"]:
            c["status"] = "CLOSED"

    with open(cases_file, "w") as f:
        json.dump(cases, f, indent=4)


    return jsonify({"message": "Case closed"})
# (previous code remains unchanged)

def close_case():
    ...
    return jsonify({"message": "Case closed"})


# ================================
# ADD THE FUNCTION HERE (👇)
# ================================

def generate_log_alerts_if_needed():
    alerts_file = os.path.join(REPORTS_DIR, 'alerts.json')
    findings_file = os.path.join(REPORTS_DIR, 'findings.txt')

    if os.path.exists(alerts_file):
        try:
            with open(alerts_file) as f:
                data = json.load(f)
                if len(data) > 0:
                    return
        except:
            pass

    alerts = []

    if not os.path.exists(findings_file):
        return

    with open(findings_file) as f:
        lines = f.read().splitlines()

    alert_id = 1
    for line in lines:
        if not line.strip():
            continue

        alerts.append({
            "alert_id": f"ALERT-LOG-{alert_id}",
            "source": "LOG",
            "severity": "HIGH",
            "description": line,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "OPEN"
        })
        alert_id += 1

    insert_alert(
    alert_id=f"ALERT-LOG-{alert_id}",
    source="LOG",
    severity="HIGH",
    description=line
)


def generate_email_alerts_if_needed():
    alerts_file = os.path.join(REPORTS_DIR, 'alerts.json')
    email_dir = os.path.join(BASE_DIR, 'uploads', 'emails')

    if not os.path.exists(email_dir):
        return

    alerts = []
    if os.path.exists(alerts_file):
        try:
            with open(alerts_file) as f:
                alerts = json.load(f)
        except:
            alerts = []

    existing_descriptions = [a["description"] for a in alerts]

    for eml in os.listdir(email_dir):
        if not eml.endswith(".eml"):
            continue

        eml_path = os.path.join(email_dir, eml)

        try:
            result = subprocess.check_output(
                ["python3", "scripts/phishguard_main.py", eml_path],
                cwd=BASE_DIR
            ).decode().strip()
        except:
            continue

        if result.upper() == "SAFE":
            continue

        severity = "MEDIUM" if result.upper() == "SUSPICIOUS" else "HIGH"
        description = f"Phishing email detected ({result}) in {eml}"

        if description in existing_descriptions:
            continue

        alerts.append({
            "alert_id": f"ALERT-EMAIL-{len(alerts)+1}",
            "source": "EMAIL",
            "severity": severity,
            "description": description,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "OPEN"
        })

        # ---- ADD PHISHING EVENT TO FORENSIC TIMELINE ----
        timeline_file = os.path.join(REPORTS_DIR, "timeline.csv")
        timeline_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, Phishing email detected ({result}) in {eml}"

        file_exists = os.path.exists(timeline_file)
        with open(timeline_file, "a") as tf:
            if not file_exists:
                tf.write("timestamp,description\n")
            tf.write(timeline_entry + "\n")


    with open(alerts_file, "w") as f:
        json.dump(alerts, f, indent=4)

# ---------------- SLA ENGINE ----------------

def get_sla_minutes(severity):
    if severity == "HIGH":
        return 15
    elif severity == "MEDIUM":
        return 60
    else:
        return 240


def calculate_sla_deadline(created_time, sla_minutes):
    created_dt = datetime.strptime(created_time, "%Y-%m-%d %H:%M:%S")
    deadline = created_dt + timedelta(minutes=sla_minutes)
    return deadline.strftime("%Y-%m-%d %H:%M:%S")


def get_sla_status(deadline):
    now = datetime.now()
    deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
    return "BREACHED" if now > deadline_dt else "ON_TRACK"

def calculate_sla_remaining(deadline_str):
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        diff = deadline - now

        seconds = int(diff.total_seconds())
        sign = "-" if seconds < 0 else ""
        seconds = abs(seconds)

        minutes = seconds // 60
        secs = seconds % 60

        return f"{sign}{minutes}m {secs}s"
    except Exception:
        return "N/A"




# =================================================
# ✅ PHASE-3 STEP-2: ALERTS API
# =================================================
@app.route("/api/alerts")
def get_alerts():
    conn = sqlite3.connect("soc.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT alert_id, source, severity, description, status, timestamp
        FROM alerts
        ORDER BY timestamp DESC
    """)

    rows = cur.fetchall()
    conn.close()

    alerts = []

    for r in rows:
        alert_id = r[0]
        source = r[1]
        severity = r[2]
        description = r[3]
        status = r[4]
        timestamp = r[5]

        # SLA CALCULATION (READ TIME)
        sla_minutes = get_sla_minutes(severity)
        sla_deadline = calculate_sla_deadline(timestamp, sla_minutes)
        sla_status = get_sla_status(sla_deadline)
        sla_remaining = calculate_sla_remaining(sla_deadline)

        alerts.append({
            "alert_id": alert_id,
            "source": source,
            "severity": severity,
            "description": description,
            "status": status,
            "timestamp": timestamp,
            "sla_deadline": sla_deadline,
            "sla_status": sla_status,
            "sla_remaining": sla_remaining,

        })

    return jsonify(alerts)


# -----------------------------
# ACKNOWLEDGE ALERT (SOC ACTION)
# -----------------------------
@app.route('/api/alerts/<alert_id>/ack', methods=['POST'])
def acknowledge_alert(alert_id):
    try:
        conn = sqlite3.connect('soc.db')
        cur = conn.cursor()

        cur.execute("""
            UPDATE alerts
            SET status = 'ACKNOWLEDGED'
            WHERE alert_id = ?
        """, (alert_id,))

        conn.commit()
        conn.close()

        return jsonify({
            "message": f"Alert {alert_id} acknowledged successfully"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# RESOLVE / CLOSE ALERT (SOC)
# -----------------------------
@app.route('/api/alerts/<alert_id>/close', methods=['POST'])
def close_alert(alert_id):
    try:
        conn = sqlite3.connect('soc.db')
        cur = conn.cursor()

        cur.execute("""
            UPDATE alerts
            SET status = 'CLOSED'
            WHERE alert_id = ?
        """, (alert_id,))

        conn.commit()
        conn.close()

        return jsonify({
            "message": f"Alert {alert_id} closed successfully"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# ADD ANALYST NOTE (SOC)
# -----------------------------
@app.route('/api/alerts/<alert_id>/notes', methods=['POST'])
def add_alert_note(alert_id):
    data = request.json
    analyst = data.get("analyst", "SOC-Analyst")
    note = data.get("note", "")

    try:
        conn = sqlite3.connect('soc.db')
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO alert_notes (alert_id, analyst, note, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (alert_id, analyst, note))

        conn.commit()
        conn.close()

        return jsonify({"message": "Note added successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# GET ALERT NOTES (SOC)
# -----------------------------
@app.route('/api/alerts/<alert_id>/notes', methods=['GET'])
def get_alert_notes(alert_id):
    try:
        conn = sqlite3.connect('soc.db')
        cur = conn.cursor()

        cur.execute("""
            SELECT analyst, note, created_at
            FROM alert_notes
            WHERE alert_id = ?
            ORDER BY created_at DESC
        """, (alert_id,))

        rows = cur.fetchall()
        conn.close()

        notes = []
        for r in rows:
            notes.append({
                "analyst": r[0],
                "note": r[1],
                "timestamp": r[2]
            })

        return jsonify(notes)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =================================================
# 🔐 INCIDENT FSM (STRICT STATE MACHINE)
# =================================================

VALID_STATES = {
    "OPEN": ["ACKNOWLEDGED"],
    "ACKNOWLEDGED": ["CLOSED"],
    "CLOSED": []
}

def is_valid_transition(old, new):
    return new in VALID_STATES.get(old, [])

@app.route("/api/alerts/<alert_id>/state", methods=["POST"])
def change_alert_state(alert_id):
    data = request.json
    new_state = data.get("state")

    if not new_state:
        return jsonify({"error": "State missing"}), 400

    conn = sqlite3.connect("soc.db")
    cur = conn.cursor()

    cur.execute("SELECT status FROM alerts WHERE alert_id=?", (alert_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Alert not found"}), 404

    old_state = row[0]

    if not is_valid_transition(old_state, new_state):
        conn.close()
        return jsonify({
            "error": "Invalid transition",
            "from": old_state,
            "allowed": VALID_STATES.get(old_state, [])
        }), 400

    cur.execute(
        "UPDATE alerts SET status=? WHERE alert_id=?",
        (new_state, alert_id)
    )
    conn.commit()
    conn.close()

    # forensic trace
    timeline = os.path.join(REPORTS_DIR, "timeline.csv")
    with open(timeline, "a") as f:
        f.write(f"{datetime.now()},{alert_id} moved {old_state} → {new_state}\n")

    return jsonify({"message": "State updated successfully"})


# =================================================
# 📊 SOC METRICS API
# =================================================

@app.route("/api/soc/metrics")
def soc_metrics():
    conn = sqlite3.connect("soc.db")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM alerts")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM alerts WHERE status='CLOSED'")
    closed = cur.fetchone()[0]

    cur.execute("""
        SELECT julianday('now') - julianday(timestamp)
        FROM alerts WHERE status='CLOSED'
    """)
    mttr_rows = cur.fetchall()

    conn.close()

    mttr = round(sum(r[0] for r in mttr_rows) / len(mttr_rows), 2) if mttr_rows else 0
    breach_rate = round(((total - closed) / total) * 100, 2) if total else 0

    return jsonify({
        "total_alerts": total,
        "closed_alerts": closed,
        "mttr_days": mttr,
        "sla_breach_rate_percent": breach_rate
    })


# =================================================
# 🚨 AUTO-ESCALATION ENGINE (SAFE BACKGROUND)
# =================================================

def auto_escalate():
    while True:
        try:
            conn = sqlite3.connect("soc.db")
            cur = conn.cursor()

            cur.execute("""
                SELECT alert_id, severity, timestamp
                FROM alerts
                WHERE status!='CLOSED'
            """)
            alerts = cur.fetchall()

            for a in alerts:
                alert_id, severity, ts = a
                mins = get_sla_minutes(severity)
                deadline = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=mins)

                if datetime.now() > deadline and severity != "HIGH":
                    cur.execute(
                        "UPDATE alerts SET severity='HIGH' WHERE alert_id=?",
                        (alert_id,)
                    )

                    with open(os.path.join(REPORTS_DIR, "timeline.csv"), "a") as f:
                        f.write(f"{datetime.now()},AUTO-ESCALATED {alert_id}\n")

            conn.commit()
            conn.close()

        except Exception:
            pass

        time.sleep(60)  # every 1 minute


threading.Thread(target=auto_escalate, daemon=True).start()


# =================================================
# 🔎 SPLUNK-STYLE SEARCH API
# =================================================

@app.route("/api/search")
def splunk_search():
    q = """
        SELECT alert_id, source, severity, description, status, timestamp
        FROM alerts WHERE 1=1
    """
    args = []

    for field in ["severity", "status", "source"]:
        if field in request.args:
            q += f" AND {field}=?"
            args.append(request.args[field])

    if "text" in request.args:
        q += " AND description LIKE ?"
        args.append(f"%{request.args['text']}%")

    conn = sqlite3.connect("soc.db")
    cur = conn.cursor()
    cur.execute(q, args)
    rows = cur.fetchall()
    conn.close()

    return jsonify([
        {
            "alert_id": r[0],
            "source": r[1],
            "severity": r[2],
            "description": r[3],
            "status": r[4],
            "timestamp": r[5]
        } for r in rows
    ])





# ==============================
# SERVE REACT FRONTEND (PRODUCTION)
# ==============================

@app.route("/")
def serve_react():
    return send_from_directory(app.template_folder, "index.html")

@app.route("/<path:path>")
def serve_static_files(path):
    full_path = os.path.join(app.template_folder, path)
    if os.path.exists(full_path):
        return send_from_directory(app.template_folder, path)
    return send_from_directory(app.template_folder, "index.html")




# -------------------------------------------------
# START APP
# -------------------------------------------------
if __name__ == "__main__":
    print("Initializing SOC database...")
    init_db()

    print("CyberSOC Backend Running -> http://127.0.0.1:5000")
    app.run(debug=True)
