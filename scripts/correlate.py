import os
import re
import json
from collections import defaultdict
from datetime import datetime

LOG_DIR = "logs"
REPORT_DIR = "reports"
CASES_FILE = os.path.join(REPORT_DIR, "cases.json")

os.makedirs(REPORT_DIR, exist_ok=True)

# ------------------------------
# Incident ID Generator
# ------------------------------
def generate_incident_id():
    counter_file = os.path.join(REPORT_DIR, "incident_counter.txt")
    if not os.path.exists(counter_file):
        with open(counter_file, "w") as f:
            f.write("1")
        return "INC-2025-0001"

    with open(counter_file, "r+") as f:
        count = int(f.read().strip())
        count += 1
        f.seek(0)
        f.write(str(count))
        f.truncate()

    return f"INC-2025-{count:04d}"

# ------------------------------
# Timestamp Extraction
# ------------------------------
def extract_timestamp_and_message(line):
    iso = re.match(r"^(\d{4}-\d{2}-\d{2}T[\d:.+]+)\s+(.*)", line)
    if iso:
        return iso.group(1), iso.group(2)

    syslog = re.match(r"^([A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(.*)", line)
    if syslog:
        return syslog.group(1), syslog.group(2)

    return "", line.strip()

# ------------------------------
# CASE MANAGEMENT HELPERS
# ------------------------------
def load_cases():
    if os.path.exists(CASES_FILE):
        with open(CASES_FILE) as f:
            return json.load(f)
    return []

def save_cases(cases):
    with open(CASES_FILE, "w") as f:
        json.dump(cases, f, indent=4)

def create_case(alert):
    cases = load_cases()
    cases.append({
        "incident_id": alert["incident_id"],
        "timestamp": alert["timestamp"],
        "severity": alert["severity"],
        "description": alert["description"],
        "status": "OPEN",
        "assigned_to": None,
        "notes": []
    })
    save_cases(cases)

def assign_analyst(incident_id, analyst):
    cases = load_cases()
    for c in cases:
        if c["incident_id"] == incident_id:
            c["assigned_to"] = analyst
            c["status"] = "IN-PROGRESS"
    save_cases(cases)

def add_note(incident_id, note):
    cases = load_cases()
    for c in cases:
        if c["incident_id"] == incident_id:
            c["notes"].append({
                "time": datetime.now().isoformat(),
                "note": note
            })
    save_cases(cases)

def close_incident(incident_id):
    cases = load_cases()
    for c in cases:
        if c["incident_id"] == incident_id:
            c["status"] = "CLOSED"
    save_cases(cases)

# ------------------------------
# Detection Engines (EXISTING)
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
                alerts.append({
                    "incident_id": generate_incident_id(),
                    "timestamp": ts,
                    "description": f"Brute-force detected from {ip}",
                    "severity": severity,
                    "ip": ip
                })
    return alerts

def detect_privilege_escalation(events):
    alerts = []
    for ts, msg in events:
        if "sudo:" in msg and "COMMAND=" in msg:
            alerts.append({
                "incident_id": generate_incident_id(),
                "timestamp": ts,
                "description": "Privilege escalation via sudo",
                "severity": "HIGH",
                "ip": "N/A"
            })
    return alerts

def detect_malware(events):
    alerts = []
    for ts, msg in events:
        if re.search(r"(wget|curl|base64|/tmp/|/dev/shm)", msg):
            alerts.append({
                "incident_id": generate_incident_id(),
                "timestamp": ts,
                "description": "Suspicious malware execution activity",
                "severity": "HIGH",
                "ip": "N/A"
            })
    return alerts

# ------------------------------
# 🔥 PHASE-2 STEP-3: Outbound Traffic Detection
# ------------------------------
def detect_suspicious_outbound(events):
    alerts = []
    outbound_hits = defaultdict(int)

    for ts, msg in events:
        m = re.search(r"(CONNECT|POST|UPLOAD|curl|wget).*?(\d+\.\d+\.\d+\.\d+)", msg)
        if m:
            ip = m.group(2)
            outbound_hits[ip] += 1
            if outbound_hits[ip] >= 3:
                alerts.append({
                    "incident_id": generate_incident_id(),
                    "timestamp": ts,
                    "description": f"Suspicious outbound traffic to {ip}",
                    "severity": "HIGH",
                    "ip": ip
                })
    return alerts

# ------------------------------
# MAIN ENGINE
# ------------------------------
def main():
    events = []

    for file in os.listdir(LOG_DIR):
        if file.endswith(".log"):
            with open(os.path.join(LOG_DIR, file), "r", errors="ignore") as f:
                for line in f:
                    ts, msg = extract_timestamp_and_message(line.strip())
                    if ts:
                        events.append((ts, msg))

    alerts = []
    alerts += detect_bruteforce(events)
    alerts += detect_privilege_escalation(events)
    alerts += detect_malware(events)
    alerts += detect_suspicious_outbound(events)  # ✅ STEP-3 added

    for alert in alerts:
        create_case(alert)

    if alerts:
        first_id = alerts[0]["incident_id"]
        assign_analyst(first_id, "SOC-Analyst-Lokeshwar")
        add_note(first_id, "Outbound traffic verified. Threat confirmed.")
        close_incident(first_id)

    with open(os.path.join(REPORT_DIR, "findings.txt"), "w") as f:
        for a in alerts:
            f.write(f"[{a['severity']}] {a['description']}\n")

    with open(os.path.join(REPORT_DIR, "timeline.csv"), "w") as f:
        f.write("Timestamp,Description\n")
        for ts, msg in events:
            f.write(f"{ts},{msg}\n")

    iocs = {
        "total_incidents": len(alerts),
        "high_severity": sum(1 for a in alerts if a["severity"] == "HIGH")
    }

    with open(os.path.join(REPORT_DIR, "iocs.json"), "w") as f:
        json.dump(iocs, f, indent=4)

    print("✅ Phase-2 Step-3 completed: Suspicious outbound traffic detection added")

if __name__ == "__main__":
    main()
