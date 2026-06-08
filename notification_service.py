"""
notification_service.py
------------------------
Out-of-app emergency delivery — reaches the phone EVEN WHEN THE BROWSER /
APP IS CLOSED, because these channels are delivered by the phone's OS, not
by in-page JavaScript.

Channels (all optional, configured via Streamlit secrets):

  1. Telegram Bot  (FREE, recommended)  -> push notification + sound on the
     phone's Telegram app, works with the browser fully closed.
  2. Twilio SMS    (optional)           -> text message to any phone.
  3. Twilio Voice  (optional)           -> an actual phone CALL that rings
     loudly and speaks the emergency — the closest thing to a "loud siren
     on a closed phone".

If nothing is configured the functions degrade gracefully (return a
"not configured" result) so the rest of the app keeps working.

Setup is documented in README.md ("Phone alerts when the app is closed").
"""

import os
import requests
import streamlit as st


# --------------------------------------------------------------------------- #
# Config helpers
# --------------------------------------------------------------------------- #
def _secret(section, key, env=None):
    try:
        if section in st.secrets and key in st.secrets[section]:
            return st.secrets[section][key]
    except Exception:
        pass
    return os.environ.get(env or f"{section.upper()}_{key.upper()}")


def telegram_configured():
    return bool(_secret("telegram", "bot_token", "TELEGRAM_BOT_TOKEN"))


def twilio_configured():
    return bool(
        _secret("twilio", "account_sid", "TWILIO_ACCOUNT_SID")
        and _secret("twilio", "auth_token", "TWILIO_AUTH_TOKEN")
        and _secret("twilio", "from_number", "TWILIO_FROM_NUMBER")
    )


# --------------------------------------------------------------------------- #
# Message body
# --------------------------------------------------------------------------- #
def build_alert_text(alert):
    maps_link = (
        f"https://www.google.com/maps?q={alert.get('latitude')},"
        f"{alert.get('longitude')}"
    )
    return (
        "🚨 EMERGENCY SOS 🚨\n"
        f"{alert.get('user_name', 'A user')} needs help NOW.\n\n"
        f"Risk: {alert.get('risk_level')} (score {alert.get('risk_score')})\n"
        f"Time: {str(alert.get('created_at',''))[:19]}\n"
        f"Battery: {alert.get('battery_level')}%\n"
        f"Location: {alert.get('address')}\n"
        f"Live map: {maps_link}\n\n"
        "Please call them and alert authorities immediately."
    )


# --------------------------------------------------------------------------- #
# 1) Telegram Bot push  (FREE — works when the browser is closed)
# --------------------------------------------------------------------------- #
def send_telegram(chat_id, text):
    """Send a Telegram message. Returns (ok, message)."""
    token = _secret("telegram", "bot_token", "TELEGRAM_BOT_TOKEN")
    if not token:
        return False, "Telegram not configured"
    if not chat_id:
        return False, "No Telegram chat_id"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(
            url,
            json={"chat_id": str(chat_id), "text": text,
                  "disable_web_page_preview": False},
            timeout=10,
        )
        if resp.ok and resp.json().get("ok"):
            return True, "Telegram push delivered"
        return False, f"Telegram error: {resp.text[:120]}"
    except Exception as exc:
        return False, f"Telegram failed: {exc}"


# --------------------------------------------------------------------------- #
# 2) Twilio SMS  (optional)
# --------------------------------------------------------------------------- #
def send_sms(to_number, text):
    if not twilio_configured():
        return False, "Twilio SMS not configured"
    sid = _secret("twilio", "account_sid", "TWILIO_ACCOUNT_SID")
    token = _secret("twilio", "auth_token", "TWILIO_AUTH_TOKEN")
    from_number = _secret("twilio", "from_number", "TWILIO_FROM_NUMBER")
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        resp = requests.post(
            url,
            data={"From": from_number, "To": to_number, "Body": text[:1500]},
            auth=(sid, token),
            timeout=12,
        )
        if resp.ok:
            return True, "SMS sent"
        return False, f"SMS error: {resp.text[:120]}"
    except Exception as exc:
        return False, f"SMS failed: {exc}"


# --------------------------------------------------------------------------- #
# 3) Twilio Voice call  (optional — RINGS the phone loudly)
# --------------------------------------------------------------------------- #
def make_call(to_number, spoken_text):
    if not twilio_configured():
        return False, "Twilio voice not configured"
    sid = _secret("twilio", "account_sid", "TWILIO_ACCOUNT_SID")
    token = _secret("twilio", "auth_token", "TWILIO_AUTH_TOKEN")
    from_number = _secret("twilio", "from_number", "TWILIO_FROM_NUMBER")
    # TwiML that speaks the alert twice
    twiml = (
        "<Response><Say voice='alice' loop='2'>"
        f"{spoken_text}"
        "</Say></Response>"
    )
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json"
        resp = requests.post(
            url,
            data={"From": from_number, "To": to_number, "Twiml": twiml},
            auth=(sid, token),
            timeout=12,
        )
        if resp.ok:
            return True, "Phone call placed"
        return False, f"Call error: {resp.text[:120]}"
    except Exception as exc:
        return False, f"Call failed: {exc}"


# --------------------------------------------------------------------------- #
# Unified dispatcher used by the SOS pipeline
# --------------------------------------------------------------------------- #
def dispatch_to_phone(alert, user, contacts):
    """
    Push the alert to every out-of-app channel that is configured, for both
    the user (self-alert) and each trusted contact.

    Returns a list of per-delivery result dicts.
    """
    text = build_alert_text(alert)
    spoken = (
        f"Emergency. {alert.get('user_name','A user')} has triggered an S O S "
        f"alert. Risk level {alert.get('risk_level')}. Please respond immediately."
    )
    results = []

    # ---- Self alert: notify the user's OWN phone ----
    self_chat = user.get("telegram_chat_id")
    if self_chat:
        ok, msg = send_telegram(self_chat, "📲 (Self alert)\n" + text)
        results.append({"to": "You (Telegram)", "channel": "telegram",
                        "ok": ok, "message": msg})

    # ---- Contacts ----
    for _, c in contacts:
        name = c.get("name", "Contact")

        chat_id = c.get("telegram_chat_id")
        if chat_id:
            ok, msg = send_telegram(chat_id, text)
            results.append({"to": f"{name} (Telegram)", "channel": "telegram",
                            "ok": ok, "message": msg})

        phone = c.get("phone")
        if phone and twilio_configured():
            ok, msg = send_sms(phone, text)
            results.append({"to": f"{name} (SMS)", "channel": "sms",
                            "ok": ok, "message": msg})
            # Place a ringing call for HIGH / CRITICAL severity
            if alert.get("risk_level") in ("High Risk", "Critical Risk"):
                okc, msgc = make_call(phone, spoken)
                results.append({"to": f"{name} (Call)", "channel": "call",
                                "ok": okc, "message": msgc})

    return results


def channels_status():
    """Human-readable summary of which out-of-app channels are live."""
    parts = []
    parts.append(("Telegram push", telegram_configured()))
    parts.append(("Twilio SMS/Call", twilio_configured()))
    return parts
