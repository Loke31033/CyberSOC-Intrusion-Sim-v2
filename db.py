import sqlite3

def get_db():
    return sqlite3.connect("soc.db", check_same_thread=False)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id TEXT UNIQUE,
        source TEXT,
        severity TEXT,
        description TEXT,
        status TEXT DEFAULT "OPEN",
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alert_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id TEXT,
        analyst TEXT,
        note TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()
    print("✅ Database Initialized")
