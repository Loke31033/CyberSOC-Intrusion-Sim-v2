import os
import re
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

# Existing Paths
LOG_DIR = "logs"
REPORT_DIR = "reports"
CASES_FILE = os.path.join(REPORT_DIR, "cases.json")
DB_PATH = "soc.db"

os.makedirs(REPORT_DIR, exist_ok=True)

# ------------------------------
# 1. EXISTING HELPERS (Unchanged)
# ------------------------------
def generate_incident_id():
    counter_file = os.path.join(REPORT_DIR, "incident_counter.txt")
    if not os.path.exists(counter_file):
        with open(counter_file, "w") as f: f.write("1")
        return "INC-2026-0001"
    with open(counter_file, "r+") as f:
        count = int(f.read().strip()) + 1
        f.seek(0); f.write(str(count)); f.truncate()
    return f"INC-2026-{count:04d}"

def extract_timestamp_and_message(line):
    iso = re.match(r"^(\d{4}-\d{2}-\d{2}T[\d:.+]+)\s+(.*)", line)
    if iso: return iso.group(1), iso.group(2)
    syslog = re.match(r"^([A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(.*)", line)
    if syslog: return syslog.group(1), syslog.group(2)
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S"), line.strip()

# ------------------------------
# 2. EXISTING DETECTION ENGINES (Unchanged)
# ------------------------------
def detect_bruteforce(events):
    failed = defaultdict(int)
    alerts = []
    for ts, msg in events:
        m = re.search(r"Failed password.*from (\d+\.\d+\.\d+\.\d+)", msg)
        if m:
            ip = m.group(1)
            failed[ip] += 1
            if failed[ip] in [3, 5]:
                severity = "MEDIUM" if failed[ip] == 3 else "HIGH"
                alerts.append({"incident_id": generate_incident_id(), "timestamp": ts, 
                               "description": f"Brute-force detected from {ip}", "severity": severity})
    return alerts

def detect_privilege_escalation(events):
    alerts = []
    for ts, msg in events:
        if "sudo:" in msg and "COMMAND=" in msg:
            alerts.append({"incident_id": generate_incident_id(), "timestamp": ts, 
                           "description": "Privilege escalation via sudo", "severity": "HIGH"})
    return alerts

def detect_malware(events):
    alerts = []
    for ts, msg in events:
        if re.search(r"(wget|curl|base64|/tmp/|/dev/shm)", msg):
            alerts.append({"incident_id": generate_incident_id(), "timestamp": ts, 
                           "description": "Suspicious malware execution activity", "severity": "HIGH"})
    return alerts

def detect_suspicious_outbound(events):
    alerts = []
    outbound_hits = defaultdict(int)
    for ts, msg in events:
        m = re.search(r"(CONNECT|POST|UPLOAD|curl|wget).*?(\d+\.\d+\.\d+\.\d+)", msg)
        if m:
            ip = m.group(2); outbound_hits[ip] += 1
            if outbound_hits[ip] >= 3:
                alerts.append({"incident_id": generate_incident_id(), "timestamp": ts, 
                               "description": f"Suspicious outbound traffic to {ip}", "severity": "HIGH"})
    return alerts

# ------------------------------
# 3. NEW: DATABASE SYNC BRIDGE
# ------------------------------
def sync_to_db(alerts):
    """Pushes detected alerts into the SQL database for the React Frontend."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for a in alerts:
        # Check if alert already exists to prevent duplicates
        cur.execute("SELECT 1 FROM alerts WHERE description = ? AND timestamp = ?", (a['description'], a['timestamp']))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO alerts (alert_id, source, severity, description, status, timestamp)
                VALUES (?, ?, ?, ?, 'OPEN', ?)
            """, (a['incident_id'], "LOG", a['severity'], a['description'], a['timestamp']))
    conn.commit()
    conn.close()

# ------------------------------
# 4. REFINED MAIN ENGINE
# ------------------------------
def main():
    events = []
    if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

    # 1. Ingest Logs
    for file in os.listdir(LOG_DIR):
        if file.endswith(".log"):
            with open(os.path.join(LOG_DIR, file), "r", errors="ignore") as f:
                for line in f:
                    ts, msg = extract_timestamp_and_message(line.strip())
                    if ts: events.append((ts, msg))

    # 2. Run All Detections
    alerts = []
    alerts += detect_bruteforce(events)
    alerts += detect_privilege_escalation(events)
    alerts += detect_malware(events)
    alerts += detect_suspicious_outbound(events)

    # 3. Persistence (JSON + SQL)
    if alerts:
        # Save to JSON (Old method)
        with open(CASES_FILE, "w") as f: json.dump(alerts, f, indent=4)
        
        # Sync to DB (New method for Frontend)
        sync_to_db(alerts)

    # 4. Generate Reports
    with open(os.path.join(REPORT_DIR, "findings.txt"), "w") as f:
        for a in alerts: f.write(f"[{a['severity']}] {a['description']}\n")

    with open(os.path.join(REPORT_DIR, "timeline.csv"), "w") as f:
        f.write("Timestamp,Description\n")
        for ts, msg in events: f.write(f"{ts},{msg}\n")

    print(f"✅ Correlation Complete. {len(alerts)} alerts processed and synced to DB.")

if __name__ == "__main__":
    main()
