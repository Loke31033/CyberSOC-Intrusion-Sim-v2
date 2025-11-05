# logs/sensor_listener.py
import requests, time, os
from datetime import datetime

# EDIT: replace with your phone IP from Phyphox remote access (no trailing slash)
PHY_BASE = "http://192.168.1.72:8080"   # <- change this to your phone IP shown by Phyphox
# many phones expose /data or dataset specific paths; this tries a few common endpoints
CANDIDATES = [
    f"{PHY_BASE}/data",
    f"{PHY_BASE}/data.json",
    f"{PHY_BASE}/api/data",
    f"{PHY_BASE}"
]

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sensor_data.log")
os.makedirs(LOG_DIR, exist_ok=True)

def fetch(url):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r
    except:
        return None

def find_endpoint():
    for u in CANDIDATES:
        r = fetch(u)
        if r is not None:
            try:
                j = r.json()
                return u
            except:
                return u
    return None

def parse_phyphox_json(data):
    # Try to find acceleration or temperature fields
    acc = None
    temp = None
    if isinstance(data, dict):
        # Generic structure: keys with 'Acceleration' etc.
        for k,v in data.items():
            kn = k.lower()
            if "accel" in kn or "acceleration" in kn:
                try:
                    acc = v.get("value", [0,0,0])
                except:
                    pass
            if "temp" in kn or "temperature" in kn:
                try:
                    temp = v.get("value", [None])[0]
                except:
                    pass
    return temp, acc

def main():
    endpoint = find_endpoint()
    if not endpoint:
        print("⚠️ Could not find Phyphox endpoint. Open Phyphox remote on phone and ensure same Wi-Fi.")
        return
    print("📡 Using Phyphox endpoint:", endpoint)
    while True:
        try:
            r = requests.get(endpoint, timeout=5)
            j = r.json()
            temp, acc = parse_phyphox_json(j)
            vib = None
            if acc:
                vib = round(sum(abs(a) for a in acc)/len(acc),2)
            ts = datetime.utcnow().isoformat()
            with open(LOG_FILE, "a") as f:
                if temp is not None:
                    f.write(f"{ts},temperature,{temp}\n")
                if vib is not None:
                    f.write(f"{ts},vibration,{vib}\n")
                    motion = 1 if vib > 0.5 else 0
                    f.write(f"{ts},motion,{motion}\n")
            print(f"[{ts}] Phyphox Temp:{temp} Vib:{vib}")
        except Exception as e:
            print("⚠️ Phyphox fetch error:", e)
        time.sleep(3)

if __name__ == "__main__":
    main()
