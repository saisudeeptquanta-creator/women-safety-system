"""User dashboard — personal safety overview."""
import streamlit as st
import plotly.express as px
import pandas as pd

from auth import require_login, current_user
from database import get_database
from ui_helpers import load_css, page_header, metric_card, sidebar_user_box

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
load_css()
require_login()
sidebar_user_box()

user = current_user()
db = get_database()
page_header(f"Welcome, {user.get('name')}", "Your safety dashboard", icon="📊")

alerts = db.get_user_alerts(user["uid"])
contacts = db.get_contacts(user["uid"])

active = sum(1 for _, a in alerts if a.get("status") == "Active")
resolved = sum(1 for _, a in alerts if a.get("status") == "Resolved")
high = sum(1 for _, a in alerts
           if a.get("risk_level") in ("High Risk", "Critical Risk"))

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Total Alerts", len(alerts), "🚨", "#7b2ff7")
with c2:
    metric_card("Active", active, "🟠", "#ff7043")
with c3:
    metric_card("Resolved", resolved, "✅", "#1faa59")
with c4:
    metric_card("High/Critical", high, "⚠️", "#d32f2f")

st.markdown("### Quick actions")
q = st.columns(5)
q[0].page_link("pages/5_SOS_Alert.py", label="🚨 SOS", use_container_width=True)
q[1].page_link("pages/4_Emergency_Contacts.py", label="👥 Contacts", use_container_width=True)
q[2].page_link("pages/6_Live_Map.py", label="🗺️ Map", use_container_width=True)
q[3].page_link("pages/8_Nearby_Safe_Places.py", label="🏥 Safe Places", use_container_width=True)
q[4].page_link("pages/7_Alert_History.py", label="📜 History", use_container_width=True)

st.markdown("---")
left, right = st.columns([3, 2])

with left:
    st.markdown("#### Recent alerts")
    if alerts:
        df = pd.DataFrame([a for _, a in alerts])
        show = df[["created_at", "risk_level", "status", "address"]].head(8)
        show.columns = ["Time", "Risk", "Status", "Location"]
        st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        st.info("No alerts yet. Stay safe! Your SOS history will appear here.")

with right:
    st.markdown("#### Risk distribution")
    if alerts:
        df = pd.DataFrame([a for _, a in alerts])
        counts = df["risk_level"].value_counts().reset_index()
        counts.columns = ["Risk", "Count"]
        fig = px.pie(
            counts, names="Risk", values="Count", hole=0.45,
            color="Risk",
            color_discrete_map={
                "Low Risk": "#1faa59",
                "Medium Risk": "#f4b400",
                "High Risk": "#ff7043",
                "Critical Risk": "#d32f2f",
            },
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Charts appear once you have alert history.")

if not contacts:
    st.warning("⚠️ You have no emergency contacts. Add at least one so we can "
               "notify someone when you trigger an SOS.")
    st.page_link("pages/4_Emergency_Contacts.py", label="➕ Add contacts now")
