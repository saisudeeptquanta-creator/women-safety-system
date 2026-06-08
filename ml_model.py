"""
ml_model.py
-----------
AI Risk Prediction engine for the Women Safety System.

Pipeline
========
1. generate_dataset()   -> synthesises a realistic, labelled training set
                           grounded in domain risk logic and writes it to
                           data/risk_training_data.csv
2. train_model()        -> trains a RandomForestClassifier, evaluates it,
                           and persists it to models/risk_model.pkl
3. predict_risk()       -> loads the cached model and returns the risk
                           level + probability for a live SOS context.

The risk LOGIC encoded in the synthetic data reflects the project spec:
    * Night time increases risk
    * Low battery increases risk
    * Repeated SOS increases risk
    * Far distance from a safe place increases risk
    * Previous incidents in the same area increase risk
    * Isolated / poorly-lit area increases risk
"""

import os
import numpy as np
import pandas as pd

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MODEL_PATH = os.path.join(MODEL_DIR, "risk_model.pkl")
TRAIN_PATH = os.path.join(DATA_DIR, "risk_training_data.csv")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Ordered list of model input features (keep order stable for inference)
FEATURES = [
    "hour",
    "is_night",
    "location_risk_score",
    "previous_incidents",
    "battery_level",
    "sos_frequency",
    "distance_to_safe_km",
    "area_type",          # 0 public, 1 residential, 2 isolated
    "is_moving",          # 1 moving, 0 stationary
]

RISK_LABELS = {0: "Low Risk", 1: "Medium Risk", 2: "High Risk", 3: "Critical Risk"}
RISK_COLORS = {
    "Low Risk": "#1faa59",
    "Medium Risk": "#f4b400",
    "High Risk": "#ff7043",
    "Critical Risk": "#d32f2f",
}


# --------------------------------------------------------------------------- #
# 1. Synthetic dataset generation
# --------------------------------------------------------------------------- #
def _score_to_label(score):
    if score < 25:
        return 0
    if score < 50:
        return 1
    if score < 75:
        return 2
    return 3


def _compute_risk_score(row):
    """Domain-driven scoring used to label synthetic samples (0-100)."""
    score = 10.0
    # Night hours (after 19:00 or before 6:00) carry more risk
    if row["is_night"]:
        score += 22
    # Low battery
    if row["battery_level"] < 20:
        score += 18
    elif row["battery_level"] < 40:
        score += 9
    # Repeated SOS in short window
    score += min(row["sos_frequency"] * 6, 18)
    # Distance to nearest safe place
    score += min(row["distance_to_safe_km"] * 4, 20)
    # Previous incidents in the area
    score += min(row["previous_incidents"] * 3, 15)
    # Area type
    score += {0: 0, 1: 6, 2: 16}[row["area_type"]]
    # Location intrinsic risk
    score += row["location_risk_score"] * 0.15
    # Stationary in isolated zone is riskier
    if row["area_type"] == 2 and row["is_moving"] == 0:
        score += 8
    return float(np.clip(score, 0, 100))


def generate_dataset(n=6000, seed=42, save=True):
    """Create a labelled training dataframe."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        hour = int(rng.integers(0, 24))
        is_night = 1 if (hour >= 19 or hour < 6) else 0
        location_risk_score = float(rng.uniform(0, 100))
        previous_incidents = int(rng.integers(0, 8))
        battery_level = int(rng.integers(2, 100))
        sos_frequency = int(rng.integers(0, 5))
        distance_to_safe_km = float(round(rng.uniform(0.1, 6.0), 2))
        area_type = int(rng.choice([0, 1, 2], p=[0.45, 0.35, 0.20]))
        is_moving = int(rng.integers(0, 2))

        row = {
            "hour": hour,
            "is_night": is_night,
            "location_risk_score": round(location_risk_score, 2),
            "previous_incidents": previous_incidents,
            "battery_level": battery_level,
            "sos_frequency": sos_frequency,
            "distance_to_safe_km": distance_to_safe_km,
            "area_type": area_type,
            "is_moving": is_moving,
        }
        score = _compute_risk_score(row)
        # Add slight noise so the boundary isn't perfectly deterministic
        score = float(np.clip(score + rng.normal(0, 4), 0, 100))
        row["risk_score"] = round(score, 2)
        row["risk_label"] = _score_to_label(score)
        rows.append(row)

    df = pd.DataFrame(rows)
    if save:
        df.to_csv(TRAIN_PATH, index=False)
    return df


# --------------------------------------------------------------------------- #
# 2. Training
# --------------------------------------------------------------------------- #
def train_model(df=None, save=True):
    """Train + evaluate the Random Forest. Returns (model, metrics)."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    import joblib

    if df is None:
        df = generate_dataset(save=save)

    X = df[FEATURES]
    y = df["risk_label"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=14,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    metrics = {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "report": classification_report(
            y_test, preds, target_names=list(RISK_LABELS.values()),
            output_dict=True, zero_division=0
        ),
        "feature_importance": dict(
            sorted(
                zip(FEATURES, model.feature_importances_),
                key=lambda x: x[1],
                reverse=True,
            )
        ),
    }

    if save:
        joblib.dump(model, MODEL_PATH)
    return model, metrics


# --------------------------------------------------------------------------- #
# 3. Inference
# --------------------------------------------------------------------------- #
_cached_model = None


def load_model():
    """Load (training on first run if necessary) and cache the model."""
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    import joblib

    if not os.path.exists(MODEL_PATH):
        train_model()
    _cached_model = joblib.load(MODEL_PATH)
    return _cached_model


def build_feature_vector(
    hour,
    location_risk_score,
    previous_incidents,
    battery_level,
    sos_frequency,
    distance_to_safe_km,
    area_type,
    is_moving,
):
    is_night = 1 if (hour >= 19 or hour < 6) else 0
    return pd.DataFrame(
        [
            {
                "hour": hour,
                "is_night": is_night,
                "location_risk_score": location_risk_score,
                "previous_incidents": previous_incidents,
                "battery_level": battery_level,
                "sos_frequency": sos_frequency,
                "distance_to_safe_km": distance_to_safe_km,
                "area_type": area_type,
                "is_moving": is_moving,
            }
        ]
    )[FEATURES]


def predict_risk(**kwargs):
    """
    Predict the risk level for a live context.
    Returns dict: { level, label_index, score, confidence, probabilities }.
    """
    model = load_model()
    X = build_feature_vector(**kwargs)
    label_index = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]
    confidence = float(round(proba[label_index] * 100, 1))

    # Derive a continuous 0-100 score from class probabilities
    score = float(round(sum(p * i for i, p in enumerate(proba)) / 3 * 100, 1))

    return {
        "level": RISK_LABELS[label_index],
        "label_index": label_index,
        "score": score,
        "confidence": confidence,
        "probabilities": {RISK_LABELS[i]: round(p * 100, 1)
                          for i, p in enumerate(proba)},
        "color": RISK_COLORS[RISK_LABELS[label_index]],
    }


def get_recommendations(level):
    """Context-aware safety recommendations per risk level."""
    base = [
        "Share your live location with a trusted contact.",
        "Stay in well-lit, populated areas.",
    ]
    extra = {
        "Low Risk": [
            "Situation appears normal — keep your phone charged.",
            "Save emergency numbers for quick access.",
        ],
        "Medium Risk": [
            "Move towards a public place such as a shop or bus stop.",
            "Keep a trusted contact on call.",
            "Avoid shortcuts through isolated streets.",
        ],
        "High Risk": [
            "Head to the nearest police station or hospital immediately.",
            "Call a trusted contact and keep the line open.",
            "Make noise / draw attention if you feel threatened.",
        ],
        "Critical Risk": [
            "🚨 Call emergency services (police/100/112) right now.",
            "Trigger the SOS alert so contacts get your live location.",
            "Get to the nearest safe place using the route guide.",
            "Use the loud siren to attract help.",
        ],
    }
    return base + extra.get(level, [])


# --------------------------------------------------------------------------- #
# CLI entry-point: `python ml_model.py` regenerates data + retrains model
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    print("Generating dataset...")
    data = generate_dataset()
    print(f"  -> {len(data)} samples written to {TRAIN_PATH}")
    print("Training Random Forest...")
    _, m = train_model(data)
    print(f"  -> Accuracy: {m['accuracy']}")
    print("  -> Top features:")
    for feat, imp in list(m["feature_importance"].items())[:5]:
        print(f"       {feat:24s} {imp:.3f}")
    print(f"Model saved to {MODEL_PATH}")
