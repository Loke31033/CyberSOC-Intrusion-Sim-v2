# 🛡️ CYBER-SOC v2.0 | Advanced Incident Response Dashboard

A professional Security Operations Center (SOC) dashboard built for real-time threat monitoring, forensic timeline reconstruction, and automated incident lifecycle management.



## 🚀 Core Features

* **Live Intrusion Feed:** Real-time monitoring of security alerts with severity classification.
* **SLA Engine:** Background watchdog that tracks incident response times and auto-escalates "MEDIUM" threats to "HIGH" if not acknowledged within 15 minutes.
* **Forensic Timeline Reconstruction:** Automatically builds an audit trail of every system event and analyst action for digital forensics.
* **Investigation Notes:** Allows analysts to attach findings, evidence, and remarks directly to a case.
* **Automated Reporting:** Generates official `.txt` forensic reports for legal and management review at the click of a button.
* **System Health Monitoring:** Tracks uptime and OS status of the monitoring node.

## 🛠️ Technical Stack

* **Frontend:** React.js, Tailwind CSS, Lucide-React (Icons)
* **Backend:** Flask (Python)
* **Database:** SQLite3 (Persistent Alert Storage)
* **Logging:** CSV-based Forensic Timeline (`timeline.csv`)
* **Automation:** Python Threading & Subprocesses

## 📊 System Architecture

1.  **Log Correlation:** Scripts parse raw logs and inject them into the SQLite database.
2.  **State Management:** Analysts transition cases through `OPEN` -> `ACKNOWLEDGED` -> `CLOSED`.
3.  **Audit Trail:** Every change is logged with a timestamp to the Forensic Timeline.
4.  **Reporting:** Backend generates memory-buffered reports filtered by Incident ID.



## 📥 Installation & Setup

### 1. Prerequisites
* Python 3.x
* Node.js & npm

### 2. Backend Setup
```bash
cd backend
pip install flask flask-cors
python app.py

3. Frontend Setup

cd frontend
npm install
npm start


