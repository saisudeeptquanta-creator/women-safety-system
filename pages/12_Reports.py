"""Reports — generate and download incident & admin PDF reports."""
import os
import streamlit as st

from auth import require_login, current_user, is_admin
from database import get_database
from ui_helpers import load_css, page_header, sidebar_user_box
import report_generator

st.set_page_config(page_title="Reports", page_icon="📄", layout="wide")
load_css()
require_login()
sidebar_user_box()

user = current_user()
db = get_database()
page_header("Reports", "Generate professional PDF documentation", icon="📄")

tabs = st.tabs(["📄 Incident reports", "📊 Admin report"] if is_admin()
               else ["📄 Incident reports"])

# --- Incident reports tab --------------------------------------------------
with tabs[0]:
    alerts = db.get_user_alerts(user["uid"]) if not is_admin() else db.get_all_alerts()
    if not alerts:
        st.info("No alerts available to report on.")
    else:
        options = {
            f"{a.get('user_name')} · {str(a.get('created_at',''))[:16]} · "
            f"{a.get('risk_level')}": (aid, a)
            for aid, a in alerts
        }
        choice = st.selectbox("Select an alert", list(options.keys()))
        aid, alert = options[choice]
        if st.button("📄 Generate incident PDF", use_container_width=True):
            path = report_generator.generate_incident_report(alert)
            st.success("Report generated.")
            with open(path, "rb") as fh:
                st.download_button(
                    "⬇️ Download incident report", fh,
                    file_name=os.path.basename(path),
                    mime="application/pdf", use_container_width=True,
                )

# --- Admin report tab ------------------------------------------------------
if is_admin():
    with tabs[1]:
        alerts = db.get_all_alerts()
        users = db.all("Users")
        stats = {
            "total_users": len(users),
            "total_alerts": len(alerts),
            "active_alerts": sum(1 for _, a in alerts if a.get("status") == "Active"),
            "resolved_alerts": sum(1 for _, a in alerts if a.get("status") == "Resolved"),
            "high_risk_alerts": sum(1 for _, a in alerts
                                    if a.get("risk_level") in ("High Risk", "Critical Risk")),
        }
        st.json(stats)
        if st.button("📊 Generate admin report", use_container_width=True):
            path = report_generator.generate_admin_report(stats, alerts)
            st.success("Admin report generated.")
            with open(path, "rb") as fh:
                st.download_button(
                    "⬇️ Download admin report", fh,
                    file_name=os.path.basename(path),
                    mime="application/pdf", use_container_width=True,
                )

# --- Previously generated reports -----------------------------------------
st.markdown("---")
st.markdown("### 🗂️ Previously generated reports")
reports = db.all("Reports")
if reports:
    for rid, r in sorted(reports, key=lambda x: x[1].get("generated_at", ""),
                         reverse=True)[:20]:
        path = r.get("report_path", "")
        name = os.path.basename(path) if path else "report"
        cols = st.columns([3, 2, 2])
        cols[0].write(f"📄 {name}")
        cols[1].write(str(r.get("generated_at", ""))[:19])
        if path and os.path.exists(path):
            with open(path, "rb") as fh:
                cols[2].download_button("⬇️", fh, file_name=name,
                                        mime="application/pdf", key=f"r_{rid}")
else:
    st.caption("No reports generated yet.")
