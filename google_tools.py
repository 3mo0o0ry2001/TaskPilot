import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from googleapiclient.discovery import build
from google_auth import get_credentials


def get_gmail_service():
    return build("gmail", "v1", credentials=get_credentials())


def get_calendar_service():
    return build("calendar", "v3", credentials=get_credentials())


def send_real_email(recipient_email: str, subject: str, body: str) -> dict:
    try:
        service = get_gmail_service()

        message = MIMEMultipart()
        message["to"] = recipient_email
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return {
            "status": "sent",
            "message_id": result["id"],
            "recipient": recipient_email,
            "subject": subject
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def create_real_event(title: str, start_time: str, duration_minutes: int = 30, description: str = "") -> dict:
    try:
        service = get_calendar_service()

        start_dt = datetime.fromisoformat(start_time)
        end_dt = start_dt.replace(
            minute=start_dt.minute + duration_minutes
        )

        event = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Asia/Dubai"
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Asia/Dubai"
            }
        }

        result = service.events().insert(
            calendarId="primary",
            body=event
        ).execute()

        return {
            "status": "created",
            "event_id": result["id"],
            "title": title,
            "start_time": start_time,
            "link": result.get("htmlLink", "")
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def read_recent_emails(max_results: int = 5) -> dict:
    try:
        service = get_gmail_service()

        results = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            labelIds=["INBOX"]
        ).execute()

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            full_msg = service.users().messages().get(
                userId="me",
                messageId=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {
                h["name"]: h["value"]
                for h in full_msg["payload"]["headers"]
            }

            emails.append({
                "id": msg["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "snippet": full_msg.get("snippet", "")
            })

        return {"status": "ok", "count": len(emails), "emails": emails}
    except Exception as e:
        return {"status": "error", "error": str(e)}