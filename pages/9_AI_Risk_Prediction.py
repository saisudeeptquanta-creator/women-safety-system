"""AI Risk Prediction — interactive Random Forest inference + explainability."""
import streamlit as st
import pandas as pd
import plotly.express as px

from auth import require_login
from ui_helpers import load_css, page_header, sidebar_user_box, risk_badge
import ml_model

st.set_page_config(page_title="AI Risk Prediction", page_icon="🤖", layout="wide")
load_css()
require_login()
sidebar_user_box()

page_header("AI Risk Prediction", "Random Forest powered risk intelligence", icon="🤖")

st.markdown("Adjust the context below and the model predicts the risk level "
            "(Low · Medium · High · Critical).")

c1, c2, c3 = st.columns(3)
with c1:
    hour = st.slider("Hour of day", 0, 23, 22)
    battery = st.slider("Battery level (%)", 1, 100, 30)
    is_moving = st.radio("Movement", ["Moving", "Stationary"], horizontal=True)
with c2:
    distance = st.slider("Distance to nearest safe place (km)", 0.1, 6.0, 3.0)
    sos_freq = st.slider("Recent SOS count (1h)", 0, 4, 1)
    prev_incidents = st.slider("Previous incidents in area", 0, 7, 2)
with c3:
    loc_risk = st.slider("Location risk score", 0, 100, 60)
    area_type = st.selectbox("Area type",
                             ["Public", "Residential", "Isolated"], index=2)

area_map = {"Public": 0, "Residential": 1, "Isolated": 2}

if st.button("🤖 Predict risk", use_container_width=True, type="primary"):
    pred = ml_model.predict_risk(
        hour=hour,
        location_risk_score=loc_risk,
        previous_incidents=prev_incidents,
        battery_level=battery,
        sos_frequency=sos_freq,
        distance_to_safe_km=distance,
        area_type=area_map[area_type],
        is_moving=1 if is_moving == "Moving" else 0,
    )

    risk_badge(pred["level"], pred["score"], pred["confidence"])

    left, right = st.columns(2)
    with left:
        st.markdown("#### Class probabilities")
        proba = pd.DataFrame(
            {"Risk": list(pred["probabilities"].keys()),
             "Probability": list(pred["probabilities"].values())}
        )
        fig = px.bar(
            proba, x="Risk", y="Probability", color="Risk",
            color_discrete_map={
                "Low Risk": "#1faa59", "Medium Risk": "#f4b400",
                "High Risk": "#ff7043", "Critical Risk": "#d32f2f",
            },
        )
        fig.update_layout(height=320, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("#### Recommendations")
        for r in ml_model.get_recommendations(pred["level"]):
            st.markdown(f"- {r}")

st.markdown("---")
with st.expander("📈 Model details & feature importance"):
    if st.button("Retrain / evaluate model"):
        with st.spinner("Training Random Forest on synthetic dataset..."):
            _, metrics = ml_model.train_model()
        ml_model._cached_model = None
        st.success(f"Trained. Accuracy = {metrics['accuracy']}")
        imp = pd.DataFrame(
            {"Feature": list(metrics["feature_importance"].keys()),
             "Importance": list(metrics["feature_importance"].values())}
        )
        fig = px.bar(imp, x="Importance", y="Feature", orientation="h")
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Model: RandomForestClassifier (200 trees). Features: hour, day/night, "
        "location risk, previous incidents, battery, SOS frequency, distance to "
        "safe place, area type, movement status."
    )
