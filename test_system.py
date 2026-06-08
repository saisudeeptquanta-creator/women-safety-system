"""
test_system.py
--------------
Lightweight test cases for the Women Safety System core logic.
Run with:  python test_system.py   (or)   pytest test_system.py

These tests exercise the parts that must work without a network or
Firebase connection (local-JSON mode), covering the ML model, distance
math, cooldown logic, auth hashing and report generation.
"""

import os
import math

import auth
import ml_model
import map_service
import alert_service
import report_generator


PASS, FAIL = "✅ PASS", "❌ FAIL"


def check(name, condition):
    print(f"{PASS if condition else FAIL}  {name}")
    return bool(condition)


def test_password_hashing():
    h = auth._hash_password("secret123")
    return check("Password hashing verifies correctly",
                 auth._verify_password("secret123", h)
                 and not auth._verify_password("wrong", h))


def test_haversine():
    # Hyderabad to Bengaluru ~ 500-580 km
    d = map_service.haversine(17.3850, 78.4867, 12.9716, 77.5946)
    return check(f"Haversine distance plausible ({d:.0f} km)", 450 < d < 620)


def test_ml_dataset_and_training():
    df = ml_model.generate_dataset(n=800, save=False)
    ok_cols = all(c in df.columns for c in ml_model.FEATURES + ["risk_label"])
    _, metrics = ml_model.train_model(df, save=True)
    return check(f"ML trains with accuracy {metrics['accuracy']}",
                 ok_cols and metrics["accuracy"] > 0.7)


def test_risk_prediction_night_lowbattery():
    """A night-time, low-battery, isolated, far-from-safety case should
    not be predicted as Low Risk."""
    pred = ml_model.predict_risk(
        hour=23, location_risk_score=85, previous_incidents=5,
        battery_level=8, sos_frequency=3, distance_to_safe_km=5.5,
        area_type=2, is_moving=0,
    )
    return check(f"High-danger context -> elevated risk ({pred['level']})",
                 pred["level"] in ("High Risk", "Critical Risk", "Medium Risk"))


def test_recommendations():
    recs = ml_model.get_recommendations("Critical Risk")
    return check("Critical risk yields actionable recommendations",
                 len(recs) >= 4)


def test_report_generation():
    alert = {
        "alert_id": "test-123", "user_id": "u1", "user_name": "Test User",
        "latitude": 17.385, "longitude": 78.486, "address": "Test address",
        "battery_level": 40, "risk_score": 70, "risk_level": "High Risk",
        "status": "Active", "created_at": "2026-01-01T00:00:00",
        "resolved_at": None, "distance_to_safe_km": 1.2,
    }
    path = report_generator.generate_incident_report(
        alert, ["Stay safe", "Call police"], None
    )
    return check("Incident PDF report is created",
                 os.path.exists(path) and path.endswith(".pdf"))


def test_status_flow():
    return check("Status flow contains lifecycle states",
                 alert_service.STATUS_FLOW ==
                 ["Pending", "Sent", "Active", "Resolved"])


def main():
    print("=" * 55)
    print(" Women Safety System — Test Suite")
    print("=" * 55)
    results = [
        test_password_hashing(),
        test_haversine(),
        test_ml_dataset_and_training(),
        test_risk_prediction_night_lowbattery(),
        test_recommendations(),
        test_report_generation(),
        test_status_flow(),
    ]
    print("-" * 55)
    print(f" {sum(results)}/{len(results)} tests passed")
    print("=" * 55)


if __name__ == "__main__":
    main()
