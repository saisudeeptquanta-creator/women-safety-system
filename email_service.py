"""
email_service.py
----------------
Emergency notification dispatcher.

Sends SOS emails to trusted contacts using free Gmail SMTP. If SMTP
credentials are not configured the service degrades gracefully into a
SIMULATED notification (logged + returned to the UI) so the alert flow
is always demonstrable, even offline.

Configure real email by adding to .streamlit/secrets.toml:

    [email]
    sender = "yourgmail@gmail.com"
    app_password = "your-16-char-app-password"

(Use a Gmail App Password, not your normal password.)
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import streamlit as st


def _get_credentials():
    sender = app_password = None
    try:
        if "email" in st.secrets:
            sender = st.secrets["email"].get("sender")
            app_password = st.secrets["email"].get("app_password")
    except Exception:
        pass
    sender = sender or os.environ.get("SMTP_SENDER")
    app_password = app_password or os.environ.get("SMTP_APP_PASSWORD")
    return sender, app_password


def build_alert_body(alert):
    """Compose the human-readable emergency message."""
    maps_link = (
        f"https://www.openstreetmap.org/?mlat={alert['latitude']}"
        f"&mlon={alert['longitude']}#map=18/{alert['latitude']}/{alert['longitude']}"
    )
    return f"""
🚨 EMERGENCY SOS ALERT 🚨

{alert.get('user_name', 'A user')} has triggered an emergency alert and may need
immediate help.

----------------------------------------
Time           : {alert.get('created_at')}
Risk Level     : {alert.get('risk_level')}  (score {alert.get('risk_score')})
Status         : {alert.get('status')}
Battery        : {alert.get('battery_level')}%
Location       : {alert.get('address')}
Coordinates    : {alert.get('latitude')}, {alert.get('longitude')}
Live Map       : {maps_link}
----------------------------------------

Please try to contact them immediately and inform local authorities if needed.

— AI-Powered Smart Women Safety & Emergency Response System
"""


def send_email(to_email, subject, body):
    """
    Send a single email. Returns (success, message).
    Falls back to simulation if credentials are absent.
    """
    sender, app_password = _get_credentials()

    if not sender or not app_password:
        # Simulated notification
        print(f"[SIMULATED EMAIL] To: {to_email}\nSubject: {subject}\n{body}\n")
        return False, f"Simulated notification sent to {to_email}"

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, app_password)
            server.sendmail(sender, to_email, msg.as_string())
        return True, f"Email sent to {to_email}"
    except Exception as exc:
        print(f"[email_service] send failed: {exc}")
        return False, f"Failed to email {to_email}: {exc}"


def notify_contacts(alert, contacts):
    """
    Notify every trusted contact about an alert.
    Returns list of per-contact result dicts.
    """
    subject = f"🚨 SOS Alert from {alert.get('user_name', 'a contact')}"
    body = build_alert_body(alert)
    results = []
    for cid, contact in contacts:
        email = contact.get("email")
        if not email:
            results.append({"name": contact.get("name"), "ok": False,
                            "message": "No email on file"})
            continue
        ok, message = send_email(email, subject, body)
        results.append(
            {
                "name": contact.get("name"),
                "phone": contact.get("phone"),
                "ok": ok,
                "message": message,
            }
        )
    return results
