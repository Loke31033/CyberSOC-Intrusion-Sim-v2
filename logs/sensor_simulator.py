# logs/sensor_simulator.py
import random, time, os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sensor_data.log")
os.makedirs(LOG_DIR, exist_ok=True)

print("🌡️ Sensor simulator started — writing to logs/sensor_data.log")
while True:
    ts = datetime.utcnow().isoformat()
    # normal temp mostly 25-35, occasional spike 75-90
    temperature = round(random.uniform(25,35),2)
    if random.random() < 0.06:
        temperature = round(random.uniform(75,90),2)
    motion = 1 if random.random() < 0.12 else 0
    vibration = round(random.uniform(0,3),2)
    if random.random() < 0.06:
        vibration = round(random.uniform(6,10),2)
    with open(LOG_FILE, "a") as f:
        f.write(f"{ts},temperature,{temperature}\n")
        f.write(f"{ts},motion,{motion}\n")
        f.write(f"{ts},vibration,{vibration}\n")
    print(f"[{ts}] Temp:{temperature} Motion:{motion} Vib:{vibration}")
    time.sleep(5)
