"""
alert_service.py
----------------
Core emergency-alert orchestration.

Responsibilities
================
* Trigger SOS alerts with a COOLDOWN to prevent duplicate spam.
* Automatically run AI risk prediction during alert creation.
* Reverse-geocode the address (Nominatim) and compute distance to the
  nearest safe place (Overpass + OSRM/Haversine).
* Persist the alert + a LocationHistory record (Firebase or local JSON).
* Notify trusted contacts (email / simulated).
* Manage alert status lifecycle: Pending -> Sent -> Active -> Resolved.
"""

import uuid
from datetime import datetime, timezone, timedelta

from database import get_database
import map_service
import ml_model
import email_service

# Minimum seconds between two SOS alerts from the same user
SOS_COOLDOWN_SECONDS = 60

STATUS_FLOW = ["Pending", "Sent", "Active", "Resolved"]


def _now():
    return datetime.now(timezone.utc)


def _parse_iso(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Cooldown
# --------------------------------------------------------------------------- #
def is_in_cooldown(user_id):
    """Return (blocked, seconds_remaining)."""
    db = get_database()
    alerts = db.get_user_alerts(user_id)
    if not alerts:
        return False, 0
    last = alerts[0][1]
    last_time = _parse_iso(last.get("created_at", ""))
    if not last_time:
        return False, 0
    if last_time.tzinfo is None:
        last_time = last_time.replace(tzinfo=timezone.utc)
    elapsed = (_now() - last_time).total_seconds()
    if elapsed < SOS_COOLDOWN_SECONDS:
        return True, int(SOS_COOLDOWN_SECONDS - elapsed)
    return False, 0


# --------------------------------------------------------------------------- #
# Risk computation helper
# --------------------------------------------------------------------------- #
def assess_risk(user_id, lat, lon, battery_level, is_moving=1):
    """Gather features and run the AI model. Returns the prediction dict."""
    db = get_database()

    # SOS frequency: alerts in the last hour
    alerts = db.get_user_alerts(user_id)
    one_hour_ago = _now() - timedelta(hours=1)
    sos_frequency = 0
    previous_incidents = len(alerts)
    for _, a in alerts:
        t = _parse_iso(a.get("created_at", ""))
        if t:
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if t > one_hour_ago:
                sos_frequency += 1

    # Distance to nearest safe place
    nearest = map_service.nearest_safe_place(lat, lon)
    if nearest:
        distance_to_safe_km = nearest["distance_km"]
        area_type = 0  # safe place nearby => more public
    else:
        distance_to_safe_km = 5.0
        area_type = 2  # nothing nearby => isolated

    # Derive an intrinsic location-risk score from coordinates fractional noise
    location_risk_score = float(abs((lat * 1000) % 100))

    hour = datetime.now().hour

    prediction = ml_model.predict_risk(
        hour=hour,
        location_risk_score=location_risk_score,
        previous_incidents=min(previous_incidents, 7),
        battery_level=battery_level,
        sos_frequency=min(sos_frequency, 4),
        distance_to_safe_km=min(distance_to_safe_km, 6.0),
        area_type=area_type,
        is_moving=is_moving,
    )
    prediction["nearest_safe_place"] = nearest
    prediction["distance_to_safe_km"] = distance_to_safe_km
    return prediction


# --------------------------------------------------------------------------- #
# Trigger SOS
# --------------------------------------------------------------------------- #
def trigger_sos(user, lat, lon, battery_level=80, is_moving=1, force=False):
    """
    Create an emergency alert end-to-end.
    Returns dict { ok, alert_id, alert, prediction, notifications, message }.
    """
    db = get_database()
    user_id = user["uid"]

    # Cooldown guard (skippable with force=True)
    if not force:
        blocked, remaining = is_in_cooldown(user_id)
        if blocked:
            return {
                "ok": False,
                "cooldown": True,
                "message": f"SOS recently sent. Please wait {remaining}s "
                           f"before triggering again.",
                "remaining": remaining,
            }

    # AI risk prediction
    prediction = assess_risk(user_id, lat, lon, battery_level, is_moving)

    # Reverse geocode
    address = map_service.reverse_geocode(lat, lon)

    alert_id = str(uuid.uuid4())
    now_iso = _now().isoformat()
    alert = {
        "alert_id": alert_id,
        "user_id": user_id,
        "user_name": user.get("name", "User"),
        "user_email": user.get("email", ""),
        "latitude": lat,
        "longitude": lon,
        "address": address,
        "battery_level": battery_level,
        "risk_score": prediction["score"],
        "risk_level": prediction["level"],
        "risk_confidence": prediction["confidence"],
        "distance_to_safe_km": prediction["distance_to_safe_km"],
        "status": "Pending",
        "created_at": now_iso,
        "resolved_at": None,
    }

    db.add("Alerts", alert, doc_id=alert_id)

    # Location history record
    db.add(
        "LocationHistory",
        {
            "location_id": str(uuid.uuid4()),
            "alert_id": alert_id,
            "user_id": user_id,
            "latitude": lat,
            "longitude": lon,
            "accuracy": 10,
            "timestamp": now_iso,
        },
    )

    # Notify trusted contacts
    contacts = db.get_contacts(user_id)
    notifications = email_service.notify_contacts(alert, contacts)

    # Update status to Sent / Active
    new_status = "Sent" if notifications else "Active"
    db.update("Alerts", alert_id, {"status": "Active"})
    alert["status"] = "Active"

    return {
        "ok": True,
        "alert_id": alert_id,
        "alert": alert,
        "prediction": prediction,
        "notifications": notifications,
        "recommendations": ml_model.get_recommendations(prediction["level"]),
        "message": "🚨 SOS alert created and contacts notified.",
    }


# --------------------------------------------------------------------------- #
# Status management
# --------------------------------------------------------------------------- #
def update_status(alert_id, status):
    db = get_database()
    updates = {"status": status}
    if status == "Resolved":
        updates["resolved_at"] = _now().isoformat()
    return db.update("Alerts", alert_id, updates)


def resolve_alert(alert_id):
    return update_status(alert_id, "Resolved")
