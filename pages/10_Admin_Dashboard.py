"""Admin monitoring dashboard — real-time alert oversight."""
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

from auth import require_admin
from database import get_database
from ui_helpers import load_css, page_header, metric_card, sidebar_user_box
import alert_service
import map_service

st.set_page_config(page_title="Admin Dashboard", page_icon="🛰️", layout="wide")
load_css()
require_admin()
sidebar_user_box()

db = get_database()
page_header("Admin Monitoring", "Real-time emergency oversight", icon="🛰️")

# Auto-refresh control
col_a, col_b = st.columns([1, 4])
if col_a.button("🔄 Refresh live data"):
    st.rerun()
col_b.caption(f"Backend: {db.status()} — live alert feed")

users = db.all("Users")
alerts = db.get_all_alerts()

total_alerts = len(alerts)
active = sum(1 for _, a in alerts if a.get("status") == "Active")
resolved = sum(1 for _, a in alerts if a.get("status") == "Resolved")
high = sum(1 for _, a in alerts
           if a.get("risk_level") in ("High Risk", "Critical Risk"))

# On a fresh deployment the store is empty — let the admin seed demo data
# so the dashboard, analytics and heatmap are immediately populated.
if not alerts:
    st.info("No alert data found (fresh deployment). Load demo data to "
            "populate the dashboard, analytics and heatmap.")
    if st.button("📦 Load demo data (users + 120 alerts)"):
        with st.spinner("Seeding demo users, contacts and alerts..."):
            import generate_sample_data as seed
            demo_users = seed.seed_users()
            seed.seed_alerts(demo_users, n=120)
        st.success("Demo data loaded.")
        st.rerun()

m = st.columns(5)
with m[0]:
    metric_card("Total Users", len(users), "👥", "#7b2ff7")
with m[1]:
    metric_card("Total Alerts", total_alerts, "🚨", "#d32f2f")
with m[2]:
    metric_card("Active", active, "🟠", "#ff7043")
with m[3]:
    metric_card("Resolved", resolved, "✅", "#1faa59")
with m[4]:
    metric_card("High/Critical", high, "⚠️", "#b71c1c")

st.markdown("---")

# Filters
st.markdown("### 🔎 Filter alerts")
f1, f2, f3 = st.columns(3)
status_f = f1.multiselect("Status", ["Pending", "Sent", "Active", "Resolved"],
                          default=["Active", "Sent", "Pending"])
risk_f = f2.multiselect("Risk", ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
                        default=["High Risk", "Critical Risk", "Medium Risk", "Low Risk"])
user_names = sorted({a.get("user_name", "—") for _, a in alerts})
user_f = f3.multiselect("User", user_names, default=user_names)

filtered = [
    (aid, a) for aid, a in alerts
    if a.get("status") in status_f
    and a.get("risk_level") in risk_f
    and a.get("user_name") in user_f
]

left, right = st.columns([3, 2])

with left:
    st.markdown(f"### 📋 Live alerts ({len(filtered)})")
    if filtered:
        df = pd.DataFrame([a for _, a in filtered])
        cols = ["created_at", "user_name", "risk_level", "status",
                "battery_level", "address"]
        cols = [c for c in cols if c in df.columns]
        view = df[cols].copy()
        view.columns = ["Time", "User", "Risk", "Status", "Battery", "Location"][:len(cols)]
        st.dataframe(view, use_container_width=True, hide_index=True, height=380)

        st.markdown("#### Resolve an active alert")
        active_alerts = [(aid, a) for aid, a in filtered
                         if a.get("status") != "Resolved"]
        if active_alerts:
            options = {f"{a.get('user_name')} · {str(a.get('created_at',''))[:16]} · "
                       f"{a.get('risk_level')}": aid for aid, a in active_alerts}
            choice = st.selectbox("Select alert", list(options.keys()))
            if st.button("✅ Mark as resolved"):
                alert_service.resolve_alert(options[choice])
                st.success("Alert resolved.")
                st.rerun()
    else:
        st.info("No alerts match the current filters.")

with right:
    st.markdown("### 🗺️ Alert locations")
    geo = [a for _, a in filtered if a.get("latitude") and a.get("longitude")]
    if geo:
        clat = sum(a["latitude"] for a in geo) / len(geo)
        clon = sum(a["longitude"] for a in geo) / len(geo)
        fmap = map_service.build_map(clat, clon, zoom=11)
        import folium
        color_by = {"Low Risk": "green", "Medium Risk": "orange",
                    "High Risk": "red", "Critical Risk": "darkred"}
        for a in geo:
            folium.Marker(
                [a["latitude"], a["longitude"]],
                popup=f"{a.get('user_name')} — {a.get('risk_level')} "
                      f"({a.get('status')})",
                icon=folium.Icon(color=color_by.get(a.get("risk_level"), "blue"),
                                 icon="exclamation", prefix="fa"),
            ).add_to(fmap)
        st_folium(fmap, use_container_width=True, height=420)
    else:
        st.caption("No geolocated alerts to display.")

st.page_link("pages/11_Analytics.py", label="📈 Open analytics & heatmap")
st.page_link("pages/12_Reports.py", label="📄 Generate admin report")
