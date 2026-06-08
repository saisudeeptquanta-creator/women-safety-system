"""Analytics & heatmap of unsafe areas."""
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium

from auth import require_admin
from database import get_database
from ui_helpers import load_css, page_header, sidebar_user_box
import map_service

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")
load_css()
require_admin()
sidebar_user_box()

db = get_database()
page_header("Alert Analytics", "Trends, hotspots and risk intelligence", icon="📈")

alerts = db.get_all_alerts()
if not alerts:
    st.info("No alert data yet. Trigger some SOS alerts or load the sample "
            "dataset to populate analytics.")
    st.stop()

df = pd.DataFrame([a for _, a in alerts])
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
df["hour"] = df["created_at"].dt.hour
df["date"] = df["created_at"].dt.date

# --- Row 1: risk + status distribution ------------------------------------
r1c1, r1c2, r1c3 = st.columns(3)

with r1c1:
    st.markdown("#### Risk level distribution")
    counts = df["risk_level"].value_counts().reset_index()
    counts.columns = ["Risk", "Count"]
    fig = px.pie(counts, names="Risk", values="Count", hole=0.45,
                 color="Risk",
                 color_discrete_map={"Low Risk": "#1faa59", "Medium Risk": "#f4b400",
                                     "High Risk": "#ff7043", "Critical Risk": "#d32f2f"})
    fig.update_layout(height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with r1c2:
    st.markdown("#### Status breakdown")
    s = df["status"].value_counts().reset_index()
    s.columns = ["Status", "Count"]
    fig = px.bar(s, x="Status", y="Count", color="Status")
    fig.update_layout(height=300, showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with r1c3:
    st.markdown("#### Alerts by hour of day")
    h = df.groupby("hour").size().reset_index(name="Count")
    fig = px.bar(h, x="hour", y="Count")
    fig.update_layout(height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

# --- Row 2: time trend -----------------------------------------------------
st.markdown("#### Alerts over time")
trend = df.groupby("date").size().reset_index(name="Count")
fig = px.line(trend, x="date", y="Count", markers=True)
fig.update_layout(height=300)
st.plotly_chart(fig, use_container_width=True)

# --- Row 3: Heatmap of unsafe areas ---------------------------------------
st.markdown("#### 🔥 Heatmap of unsafe areas")
geo = df.dropna(subset=["latitude", "longitude"])
if len(geo):
    clat = geo["latitude"].mean()
    clon = geo["longitude"].mean()
    fmap = map_service.build_map(clat, clon, zoom=11)
    try:
        from folium.plugins import HeatMap
        weights = geo["risk_level"].map(
            {"Low Risk": 0.3, "Medium Risk": 0.6,
             "High Risk": 0.85, "Critical Risk": 1.0}
        ).fillna(0.5)
        heat = list(zip(geo["latitude"], geo["longitude"], weights))
        HeatMap(heat, radius=18, blur=14).add_to(fmap)
    except Exception:
        pass
    st_folium(fmap, use_container_width=True, height=450)

    # High-risk zone table
    st.markdown("#### 🚩 High-risk zones")
    hr = geo[geo["risk_level"].isin(["High Risk", "Critical Risk"])]
    if len(hr):
        zone = (
            hr.groupby(hr["address"].str.slice(0, 40))
            .size().reset_index(name="Incidents")
            .sort_values("Incidents", ascending=False).head(10)
        )
        zone.columns = ["Area", "Incidents"]
        st.dataframe(zone, use_container_width=True, hide_index=True)
    else:
        st.caption("No high-risk incidents recorded yet.")
else:
    st.caption("No geolocated alerts available for heatmap.")
