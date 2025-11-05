import csv
import json
import matplotlib.pyplot as plt
import os

timeline_path = os.path.join("reports", "timeline.csv")
iocs_path = os.path.join("reports", "iocs.json")

print("[+] Indicators of Compromise (IOCs):")

if os.path.exists(iocs_path):
    with open(iocs_path) as f:
        iocs = json.load(f)
        for key, value in iocs.items():
            print(f"- {key}")
else:
    print("[!] iocs.json not found")

# Parse timeline.csv
timestamps = []
descriptions = []

if os.path.exists(timeline_path):
    with open(timeline_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Timestamp"] and row["Description"]:
                timestamps.append(row["Timestamp"])
                descriptions.append(row["Description"])
else:
    print("[!] timeline.csv not found")

if timestamps:
    print(f"[+] Found {len(timestamps)} events in timeline.csv")

    # Optional: show bar chart of attack frequency by timestamp
    plt.figure(figsize=(10, 4))
    plt.hist(timestamps, bins=10, color='skyblue', edgecolor='black')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Timestamps")
    plt.ylabel("Number of Events")
    plt.title("Brute-force Attempt Timeline")
    plt.tight_layout()
    plt.show()
else:
    print("[!] No events found in timeline.csv. Try re-checking your logs.")

