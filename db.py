import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "taskpilot.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            due_date TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            start_time TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 30,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS sent_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_email TEXT NOT NULL,
            subject TEXT,
            body TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("SELECT COUNT(*) FROM contacts")
    if cur.fetchone()[0] == 0:
        seed_data(cur)

    conn.commit()
    conn.close()


def seed_data(cur):
    contacts = [
        ("Ahmed Hassan", "ahmed.hassan@example.com"),
        ("Sara Mohamed", "sara.m@example.com"),
        ("Omar Khaled", "omar.k@example.com"),
        ("Fatima Ali", "fatima.ali@example.com"),
    ]
    cur.executemany("INSERT INTO contacts (name, email) VALUES (?, ?)", contacts)

    tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
    next_week = (datetime.now() + timedelta(days=7)).isoformat()

    tasks = [
        ("Review quarterly report", next_week, "pending"),
        ("Prepare presentation slides", tomorrow, "pending"),
    ]
    cur.executemany(
        "INSERT INTO tasks (title, due_date, status) VALUES (?, ?, ?)", tasks
    )


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")