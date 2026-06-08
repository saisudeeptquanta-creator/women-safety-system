"""SOS Alert trigger — the heart of the system."""
import os
import streamlit as st

from auth import require_login, current_user
from database import get_database
from ui_helpers import (
    load_css, page_header, sidebar_user_box, location_input, risk_badge,
    fire_browser_alert,
)
import alert_service
import report_generator

st.set_page_config(page_title="SOS Alert", page_icon="🚨", layout="wide")
load_css()
require_login()
sidebar_user_box()

user = current_user()
db = get_database()
page_header("Emergency SOS", "One click to alert your trusted contacts", icon="🚨")

contacts = db.get_contacts(user["uid"])
if not contacts:
    st.warning("⚠️ You have no emergency contacts. Add one first so we can "
               "notify someone.")
    st.page_link("pages/4_Emergency_Contacts.py", label="➕ Add contacts")

# --- Location + device context ---------------------------------------------
left, right = st.columns([3, 2])
with left:
    lat, lon = location_input(key="sos")
with right:
    st.caption("📱 Device context")
    battery = st.slider("Battery level (%)", 1, 100, 65)
    moving = st.radio("Movement", ["Moving", "Stationary"], horizontal=True)
    is_moving = 1 if moving == "Moving" else 0

# Cooldown indicator
blocked, remaining = alert_service.is_in_cooldown(user["uid"])
if blocked:
    st.info(f"⏳ Cooldown active — next SOS available in {remaining}s "
            "(prevents duplicate alerts).")

st.markdown("<div class='ws-sos-wrap'>", unsafe_allow_html=True)
trigger = st.button("🚨  TRIGGER SOS  🚨", use_container_width=True,
                    type="primary", disabled=blocked)
st.markdown("</div>", unsafe_allow_html=True)

force = st.checkbox("Override cooldown (force send)", value=False)

if trigger or (force and st.session_state.get("force_clicked")):
    with st.spinner("Assessing risk, locating you and notifying contacts..."):
        result = alert_service.trigger_sos(
            user, lat, lon, battery_level=battery,
            is_moving=is_moving, force=force,
        )

    if not result["ok"]:
        st.error(result["message"])
    else:
        st.session_state["last_alert"] = result
        alert = result["alert"]
        pred = result["prediction"]

        st.success(result["message"])

        # 🔴 REAL-TIME device alert: vibration + siren sound + notification
        fire_browser_alert(
            title="🚨 SOS TRIGGERED",
            message=f"{pred['level']} · {alert['address'][:40]} · contacts notified",
        )

        # Also play the mp3 siren if the asset is present
        siren = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             "assets", "siren.mp3")
        if os.path.exists(siren):
            st.audio(siren, autoplay=True)

        risk_badge(pred["level"], pred["score"], pred["confidence"])

        m1, m2, m3 = st.columns(3)
        m1.metric("📍 Address", "Located", alert["address"][:30] + "…")
        m2.metric("🔋 Battery", f"{battery}%")
        m3.metric("🏥 Nearest safe place",
                  f"{alert['distance_to_safe_km']} km")

        st.markdown("#### 🛟 Safety recommendations")
        for r in result["recommendations"]:
            st.markdown(f"- {r}")

        st.markdown("#### 📨 Contacts notified")
        if result["notifications"]:
            for n in result["notifications"]:
                icon = "✅" if n["ok"] else "📭"
                st.write(f"{icon} **{n['name']}** — {n['message']}")
        else:
            st.write("No contacts to notify.")

        # PDF report
        if st.button("📄 Generate incident PDF report"):
            path = report_generator.generate_incident_report(
                alert, result["recommendations"], result["notifications"]
            )
            with open(path, "rb") as fh:
                st.download_button(
                    "⬇️ Download report", fh, file_name=os.path.basename(path),
                    mime="application/pdf", use_container_width=True,
                )

# Show last alert summary if exists
elif st.session_state.get("last_alert"):
    st.caption("Last alert this session:")
    a = st.session_state["last_alert"]["alert"]
    risk_badge(a["risk_level"], a["risk_score"])
    st.write(f"📍 {a['address']}  ·  {a['created_at'][:19]}")
