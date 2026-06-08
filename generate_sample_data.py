"""
generate_sample_data.py
------------------------
Populates the system with realistic demo data so every dashboard,
chart, heatmap and report is fully populated on first run.

It creates:
    * data/sample_users.csv
    * data/sample_alerts.csv
    * Seeds the local JSON / Firebase store with users, contacts,
      alerts and location history (so the admin dashboard is alive).
    * Regenerates the ML training dataset + trains the model.

Run:
    python generate_sample_data.py
"""

import os
import uuid
import random
from datetime import datetime, timezone, timedelta

import pandas as pd

import ml_model
from auth import register_user, ensure_default_admin
from database import get_database

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Demo cities (lat, lon) to scatter alerts around
CITIES = {
    "Hyderabad": (17.3850, 78.4867),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
}

RISK_LEVELS = ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"]
STATUSES = ["Pending", "Sent", "Active", "Resolved"]

SAMPLE_USERS = [
    ("Aisha Khan", "aisha@example.com", "9876500001"),
    ("Priya Sharma", "priya@example.com", "9876500002"),
    ("Meera Nair", "meera@example.com", "9876500003"),
    ("Sara Thomas", "sara@example.com", "9876500004"),
    ("Divya Rao", "divya@example.com", "9876500005"),
]


def seed_users():
    rows = []
    db = get_database()
    for name, email, phone in SAMPLE_USERS:
        uid_existing, _ = db.get_user_by_email(email)
        if uid_existing:
            uid = uid_existing
        else:
            ok, uid = register_user(name, email, phone, "password123", "user")
        # add a couple of emergency contacts each
        if not db.get_contacts(uid):
            for i in range(2):
                db.add("EmergencyContacts", {
                    "contact_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "name": f"{name.split()[0]}'s Contact {i+1}",
                    "phone": f"99999{random.randint(10000, 99999)}",
                    "email": f"contact{i+1}.{email}",
                    "relation": random.choice(["Father", "Friend", "Sister", "Mother"]),
                })
        rows.append({"uid": uid, "name": name, "email": email,
                     "phone": phone, "role": "user"})
    pd.DataFrame(rows).to_csv(os.path.join(DATA_DIR, "sample_users.csv"), index=False)
    return rows


def seed_alerts(users, n=120):
    db = get_database()
    rows = []
    now = datetime.now(timezone.utc)
    for _ in range(n):
        user = random.choice(users)
        city = random.choice(list(CITIES.keys()))
        base_lat, base_lon = CITIES[city]
        lat = base_lat + random.uniform(-0.08, 0.08)
        lon = base_lon + random.uniform(-0.08, 0.08)
        created = now - timedelta(days=random.randint(0, 29),
                                  hours=random.randint(0, 23),
                                  minutes=random.randint(0, 59))
        risk = random.choices(RISK_LEVELS, weights=[3, 3, 2, 1])[0]
        status = random.choices(STATUSES, weights=[1, 1, 2, 3])[0]
        battery = random.randint(5, 100)
        score = {"Low Risk": random.uniform(5, 24),
                 "Medium Risk": random.uniform(25, 49),
                 "High Risk": random.uniform(50, 74),
                 "Critical Risk": random.uniform(75, 100)}[risk]
        alert_id = str(uuid.uuid4())
        alert = {
            "alert_id": alert_id,
            "user_id": user["uid"],
            "user_name": user["name"],
            "user_email": user["email"],
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "address": f"{city} area, near sector {random.randint(1, 40)}",
            "battery_level": battery,
            "risk_score": round(score, 1),
            "risk_level": risk,
            "risk_confidence": round(random.uniform(70, 99), 1),
            "distance_to_safe_km": round(random.uniform(0.2, 5.5), 2),
            "status": status,
            "created_at": created.isoformat(),
            "resolved_at": (created + timedelta(hours=2)).isoformat()
            if status == "Resolved" else None,
        }
        db.add("Alerts", alert, doc_id=alert_id)
        db.add("LocationHistory", {
            "location_id": str(uuid.uuid4()),
            "alert_id": alert_id,
            "user_id": user["uid"],
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "accuracy": random.randint(5, 30),
            "timestamp": created.isoformat(),
        })
        rows.append(alert)
    pd.DataFrame(rows).to_csv(os.path.join(DATA_DIR, "sample_alerts.csv"), index=False)
    return rows


def main():
    print("Ensuring default admin (admin@safety.com / admin123)...")
    ensure_default_admin()

    print("Seeding demo users + contacts...")
    users = seed_users()
    print(f"  -> {len(users)} users")

    print("Seeding demo alerts + location history...")
    alerts = seed_alerts(users, n=120)
    print(f"  -> {len(alerts)} alerts")

    print("Generating ML training dataset + training Random Forest...")
    df = ml_model.generate_dataset()
    _, metrics = ml_model.train_model(df)
    print(f"  -> dataset: {len(df)} rows | model accuracy: {metrics['accuracy']}")

    print("\nDone. Run the app with:  streamlit run app.py")


if __name__ == "__main__":
    main()
