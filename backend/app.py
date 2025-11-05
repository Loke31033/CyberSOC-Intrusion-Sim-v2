from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import os, json, threading, subprocess, psutil, platform, time, random
from datetime import datetime

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

@app.route('/')
def index():
    return "✅ CyberSOC + Smart Sensor Flask API running"

@app.route('/api/iocs')
def get_iocs():
    path = os.path.join(REPORTS_DIR, 'iocs.json')
    if not os.path.exists(path):
        return jsonify({})
    with open(path) as f:
        return jsonify(json.load(f))

@app.route('/api/findings')
def get_findings():
    path = os.path.join(REPORTS_DIR, 'findings.txt')
    if not os.path.exists(path):
        return jsonify([])
    with open(path) as f:
        return jsonify(f.read().splitlines())

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
                timeline.append({"timestamp": timestamp, "description": desc})
    return jsonify(timeline)

# ✅ Enhanced Smart Sensor API with live simulation
@app.route('/api/sensors')
def get_sensors():
    """
    Returns live Smart Sensor readings.
    Reads from reports/sensor_findings.txt if exists,
    else dynamically generates live temperature, motion, vibration values.
    """
    sensor_file = os.path.join(REPORTS_DIR, 'sensor_findings.txt')
    findings = []

    # If real or old findings exist, load them
    if os.path.exists(sensor_file):
        with open(sensor_file) as f:
            findings = [l for l in f.read().splitlines() if l.strip()]

    # 🧠 Generate live sensor readings
    temp = round(random.uniform(20, 80), 2)      # °C
    vib = round(random.uniform(0, 10), 2)        # vibration level
    motion = random.choice([0, 1])               # 0 = none, 1 = detected
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sensor_readings = {
        "timestamp": now,
        "temperature": temp,
        "vibration": vib,
        "motion": motion
    }

    # ⚠️ Detect anomalies
    if temp > 70 or temp < 0:
        findings.append(f"🔥 Abnormal temperature {temp}°C detected at {now}")
    if vib > 7:
        findings.append(f"⚠️ High vibration {vib} detected at {now}")
    if motion == 1:
        findings.append(f"🚨 Motion detected at {now}")

    # Save only last 10 alerts
    with open(sensor_file, "w") as f:
        for line in findings[-10:]:
            f.write(line + "\n")

    # 📊 Maintain rolling history for chart data
    history_file = os.path.join(REPORTS_DIR, 'sensor_history.json')
    history = {"temp": [], "vib": [], "motion": []}
    if os.path.exists(history_file):
        try:
            with open(history_file) as f:
                history = json.load(f)
        except:
            pass

    # Append new data
    history["temp"].append(temp)
    history["vib"].append(vib)
    history["motion"].append(motion)
    # Keep only last 20 samples
    if len(history["temp"]) > 20:
        history["temp"] = history["temp"][-20:]
        history["vib"] = history["vib"][-20:]
        history["motion"] = history["motion"][-20:]

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    return jsonify({
        "sensor_findings": findings[-10:],
        "sensor_stats": history,
        "live": sensor_readings
    })

@app.route('/api/system_health')
def system_health():
    uptime_seconds = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
    uptime_hours = round(uptime_seconds / 3600, 2)
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    info = {
        "os": platform.system(),
        "uptime_hours": uptime_hours,
        "cpu_usage": cpu,
        "memory_usage": mem,
        "disk_usage": disk
    }
    return jsonify(info)

@app.route('/api/download/json')
def download_json():
    path = os.path.join(REPORTS_DIR, 'iocs.json')
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, mimetype='application/json', as_attachment=True, download_name='iocs.json')

@app.route('/api/download/csv')
def download_csv():
    path = os.path.join(REPORTS_DIR, 'timeline.csv')
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, mimetype='text/csv', as_attachment=True, download_name='timeline.csv')

@app.route('/api/filter_timeline')
def filter_timeline():
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return jsonify({"error": "Please provide start and end datetime"}), 400
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400
    path = os.path.join(REPORTS_DIR, 'timeline.csv')
    if not os.path.exists(path):
        return jsonify([])
    filtered = []
    with open(path) as f:
        next(f, None)
        for line in f:
            parts = line.strip().split(",", 1)
            if len(parts) == 2:
                timestamp, desc = parts
                try:
                    log_dt = datetime.fromisoformat(timestamp)
                    if start_dt <= log_dt <= end_dt:
                        filtered.append({"timestamp": timestamp, "description": desc})
                except Exception:
                    continue
    return jsonify(filtered)

# --- Auto-start sensor listener (tries Phyphox listener, falls back to simulator if requested) ---
def start_sensor_listener():
    logs_dir = os.path.join(BASE_DIR, "logs")
    phy = os.path.join(logs_dir, "sensor_listener.py")
    sim = os.path.join(logs_dir, "sensor_simulator.py")
    # Prefer phyphox listener if exists, else start simulator
    if os.path.exists(phy):
        try:
            print("📡 Starting sensor_listener.py (Phyphox) ...")
            subprocess.Popen(["python3", phy], cwd=logs_dir)
        except Exception as e:
            print("❌ failed to start sensor_listener.py:", e)
            if os.path.exists(sim):
                print("📡 Starting sensor_simulator.py instead ...")
                subprocess.Popen(["python3", sim], cwd=logs_dir)
    elif os.path.exists(sim):
        try:
            print("📡 Starting sensor_simulator.py ...")
            subprocess.Popen(["python3", sim], cwd=logs_dir)
        except Exception as e:
            print("❌ failed to start sensor_simulator.py:", e)
    else:
        print("⚠️ No sensor listener or simulator found in logs/ — create logs/sensor_simulator.py or logs/sensor_listener.py")

if __name__ == '__main__':
    # start background sensor process, then Flask
    threading.Thread(target=start_sensor_listener, daemon=True).start()
    print("✅ Flask starting ... (API ready on http://127.0.0.1:5000)")
    app.run(debug=True)
