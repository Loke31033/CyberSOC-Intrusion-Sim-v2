# auto_correlate.py
import os, time, subprocess
from plyer import notification

REPORTS = "reports"
SCRIPTS = "scripts"

def notify(title, msg):
    try:
        notification.notify(title=title, message=msg, timeout=6)
    except Exception:
        print("notify:", title, msg)

last_findings = set()
last_sensor = set()

print("🧠 Auto-correlate started (every 30s). Ctrl+C to stop.")
while True:
    try:
        subprocess.run(["python3", os.path.join(SCRIPTS, "correlate.py"), "logs", REPORTS], check=True)
    except Exception as e:
        print("correlate error:", e)
    # check findings
    fpath = os.path.join(REPORTS, "findings.txt")
    if os.path.exists(fpath):
        with open(fpath) as f:
            items = set(l for l in f.read().splitlines() if l.strip())
            new = items - last_findings
            for it in new:
                notify("🚨 SOC Alert", it)
            last_findings = items
    spath = os.path.join(REPORTS, "sensor_findings.txt")
    if os.path.exists(spath):
        with open(spath) as f:
            items = set(l for l in f.read().splitlines() if l.strip())
            new = items - last_sensor
            for it in new:
                notify("🌡️ Sensor Alert", it)
            last_sensor = items
    time.sleep(30)
