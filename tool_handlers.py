from datetime import datetime
from db import get_connection

# Try to import real Google tools
try:
    from google_tools import send_real_email, create_real_event, read_recent_emails
    GOOGLE_AVAILABLE = True
except Exception:
    GOOGLE_AVAILABLE = False


def find_contact(name: str) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email FROM contacts WHERE name LIKE ?",
        (f"%{name}%",)
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {"status": "not_found", "message": f"No contact found matching '{name}'"}
    return {"status": "ok", "matches": [dict(r) for r in rows]}


def send_email(recipient_email: str, subject: str, body: str) -> dict:
    if GOOGLE_AVAILABLE:
        return send_real_email(recipient_email, subject, body)

    # Fallback to mock
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sent_emails (recipient_email, subject, body) VALUES (?, ?, ?)",
        (recipient_email, subject, body)
    )
    email_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"status": "sent", "email_id": email_id, "recipient": recipient_email, "subject": subject}


def create_task(title: str, due_date: str = None) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
        (title, due_date)
    )
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"status": "created", "task_id": task_id, "title": title, "due_date": due_date}


def list_tasks(status: str = None) -> dict:
    # Models sometimes pass an empty object/dict or empty string instead of
    # omitting the optional arg. Treat anything that isn't a valid status string
    # as "no filter" (list all tasks).
    if not isinstance(status, str) or status not in ("pending", "completed"):
        status = None

    conn = get_connection()
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM tasks WHERE status = ?", (status,))
    else:
        cur.execute("SELECT * FROM tasks")
    rows = cur.fetchall()
    conn.close()
    return {"status": "ok", "count": len(rows), "tasks": [dict(r) for r in rows]}


def create_event(title: str, start_time: str, duration_minutes: int = 30, description: str = "") -> dict:
    if GOOGLE_AVAILABLE:
        return create_real_event(title, start_time, duration_minutes, description)

    # Fallback to mock
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (title, start_time, duration_minutes, description) VALUES (?, ?, ?, ?)",
        (title, start_time, duration_minutes, description)
    )
    event_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"status": "created", "event_id": event_id, "title": title, "start_time": start_time}


def get_current_datetime() -> dict:
    return {
        "current_datetime": datetime.now().isoformat(),
        "day_of_week": datetime.now().strftime("%A")
    }


def get_recent_emails(max_results: int = 5) -> dict:
    if GOOGLE_AVAILABLE:
        return read_recent_emails(max_results)
    return {"status": "error", "error": "Gmail not connected"}


TOOL_REGISTRY = {
    "find_contact": find_contact,
    "send_email": send_email,
    "create_task": create_task,
    "list_tasks": list_tasks,
    "create_event": create_event,
    "get_current_datetime": get_current_datetime,
    "get_recent_emails": get_recent_emails,
}