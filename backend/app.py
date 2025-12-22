from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import os, json, threading, subprocess, psutil, platform, time, random
from datetime import datetime
from flask import send_from_directory

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

    with open(alerts_file, "w") as f:
        json.dump(alerts, f, indent=4)

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


# =================================================
# ✅ PHASE-3 STEP-2: ALERTS API
# =================================================
@app.route('/api/alerts')
def get_alerts():
    generate_log_alerts_if_needed()   # ← ONLY NEW LINE

    alerts_file = os.path.join(REPORTS_DIR, 'alerts.json')
    if not os.path.exists(alerts_file):
        return jsonify([])

    try:
        with open(alerts_file) as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)})


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
    print("✅ CyberSOC Backend Running → http://127.0.0.1:5000")
    app.run(debug=True)
