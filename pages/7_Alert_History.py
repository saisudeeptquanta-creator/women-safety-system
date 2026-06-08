"""Alert history — view, filter, resolve and report on past alerts."""
import os
import streamlit as st
import pandas as pd

from auth import require_login, current_user
from database import get_database
from ui_helpers import load_css, page_header, sidebar_user_box, risk_badge
import alert_service
import report_generator

st.set_page_config(page_title="Alert History", page_icon="📜", layout="wide")
load_css()
require_login()
sidebar_user_box()

user = current_user()
db = get_database()
page_header("Alert History", "Your past emergency alerts", icon="📜")

alerts = db.get_user_alerts(user["uid"])
if not alerts:
    st.info("No alerts yet.")
    st.stop()

# Filters
f1, f2 = st.columns(2)
status_filter = f1.multiselect(
    "Status", ["Pending", "Sent", "Active", "Resolved"],
    default=["Pending", "Sent", "Active", "Resolved"],
)
risk_filter = f2.multiselect(
    "Risk level",
    ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
    default=["Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
)

filtered = [
    (aid, a) for aid, a in alerts
    if a.get("status") in status_filter and a.get("risk_level") in risk_filter
]

st.caption(f"Showing {len(filtered)} of {len(alerts)} alerts.")

for aid, a in filtered:
    with st.container(border=True):
        top = st.columns([3, 2, 2, 2])
        top[0].markdown(f"**{a.get('address','')[:45]}**")
        top[1].write(f"🕒 {str(a.get('created_at',''))[:19]}")
        top[2].write(f"🔋 {a.get('battery_level','—')}%")
        top[3].write(f"Status: **{a.get('status','—')}**")

        risk_badge(a.get("risk_level", "—"), a.get("risk_score"))

        actions = st.columns(3)
        if a.get("status") != "Resolved":
            if actions[0].button("✅ Mark resolved", key=f"res_{aid}"):
                alert_service.resolve_alert(aid)
                st.rerun()
        if actions[1].button("📄 PDF report", key=f"pdf_{aid}"):
            path = report_generator.generate_incident_report(a)
            with open(path, "rb") as fh:
                actions[1].download_button(
                    "⬇️ Download", fh, file_name=os.path.basename(path),
                    mime="application/pdf", key=f"dl_{aid}",
                )
        actions[2].write(f"📍 {a.get('latitude')}, {a.get('longitude')}")
