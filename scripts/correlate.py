#!/usr/bin/env python3
# scripts/correlate.py
import os
import re
import json
from collections import defaultdict
from datetime import datetime

# Input args optional: logs_dir reports_dir
import sys
if len(sys.argv) >= 3:
    LOG_DIR = sys.argv[1]
    REPORT_DIR = sys.argv[2]
else:
    LOG_DIR = "logs"
    REPORT_DIR = "reports"

os.makedirs(REPORT_DIR, exist_ok=True)

def extract_timestamp_and_message(line):
    # ISO format
    if re.match(r"^\d{4}-\d{2}-\d{2}T", line):
        try:
            timestamp, rest = line.split(" ", 1)
            return timestamp, rest.strip()
        except:
            return "", line.strip()
    # syslog
    elif re.match(r"^[A-Z][a-z]{2} +\d{1,2} \d{2}:\d{2}:\d{2}", line):
        try:
            parts = line.split(" ", 4)
            timestamp = " ".join(parts[:3])
            message = parts[4] if len(parts) > 4 else ""
            return timestamp, message.strip()
        except:
            return "", line.strip()
    else:
        return "", line.strip()

def detect_bruteforce(events):
    failed_logins = defaultdict(int)
    attacker_ips = set()
    findings = []
    for ts, msg in events:
        match = re.search(r"Failed password.*from (\d+\.\d+\.\d+\.\d+)", msg)
        if match:
            ip = match.group(1)
            failed_logins[ip] += 1
            if failed_logins[ip] >= 3:
                findings.append(f"🔴 Brute-force detected from {ip}: {failed_logins[ip]} failed attempts")
                attacker_ips.add(ip)
    return findings, list(attacker_ips)

def detect_sensor_anomalies(sensor_file):
    findings = []
    if not os.path.exists(sensor_file):
        return findings
    with open(sensor_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 3:
                continue
            ts, typ, val = parts[0], parts[1], parts[2]
            try:
                if typ == "temperature":
                    v = float(val)
                    if v > 70 or v < 0:
                        findings.append(f"🔥 Abnormal temperature {v}°C detected at {ts}")
                elif typ == "motion":
                    if val.strip() == "1":
                        findings.append(f"🚨 Motion detected at {ts}")
                elif typ == "vibration":
                    v = float(val)
                    if v > 5:
                        findings.append(f"⚠️ Excessive vibration ({v}) detected at {ts}")
            except:
                continue
    return findings

def main():
    events = []
    # Parse SSH/auth logs and other .log files
    if os.path.exists(LOG_DIR):
        for fname in sorted(os.listdir(LOG_DIR)):
            if fname.endswith(".log"):
                path = os.path.join(LOG_DIR, fname)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if "Failed password" in line or "Accepted password" in line or "Failed" in line:
                                ts, msg = extract_timestamp_and_message(line.strip())
                                events.append((ts or datetime.utcnow().isoformat(), msg))
                except Exception:
                    continue

    # Brute-force detection
    findings, attacker_ips = detect_bruteforce(events)

    # Sensor anomalies
    sensor_file = os.path.join(LOG_DIR, "sensor_data.log")
    sensor_findings = detect_sensor_anomalies(sensor_file)

    # Write timeline.csv
    timeline_path = os.path.join(REPORT_DIR, "timeline.csv")
    with open(timeline_path, "w") as f:
        f.write("Timestamp,Description\n")
        for ts, msg in events:
            # escape commas in msg
            desc = msg.replace(",", " ")
            f.write(f"{ts},{desc}\n")

    # Write iocs.json
    iocs = {
        "attacker_ips": attacker_ips,
        "compromised_users": list(set(re.findall(r"Accepted password for (\w+)", "\n".join([e[1] for e in events])))),
        "targets": list(set(re.findall(r"from (\d+\.\d+\.\d+\.\d+)", "\n".join([e[1] for e in events]))))
    }
    with open(os.path.join(REPORT_DIR, "iocs.json"), "w") as f:
        json.dump(iocs, f, indent=2)

    # Write findings.txt
    with open(os.path.join(REPORT_DIR, "findings.txt"), "w") as f:
        for item in findings:
            f.write(item + "\n")

    # Write sensor_findings.txt
    with open(os.path.join(REPORT_DIR, "sensor_findings.txt"), "w") as f:
        for item in sensor_findings:
            f.write(item + "\n")

    print(f"[+] Parsed {len(events)} events")
    print(f"[+] Correlations found: {len(findings)}")
    print(f"[+] Smart Sensor anomalies: {len(sensor_findings)}")
    print(f"[✓] Wrote: {timeline_path}")
    print(f"[✓] Wrote: {os.path.join(REPORT_DIR, 'iocs.json')}")
    print(f"[✓] Wrote: {os.path.join(REPORT_DIR, 'findings.txt')}")
    print(f"[✓] Wrote: {os.path.join(REPORT_DIR, 'sensor_findings.txt')}")

if __name__ == "__main__":
    main()
