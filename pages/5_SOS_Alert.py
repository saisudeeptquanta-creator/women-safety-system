"""SOS Alert trigger — the heart of the system (life-safety grade)."""
import os
import streamlit as st

from auth import require_login, current_user
from database import get_database
from ui_helpers import (
    load_css, page_header, sidebar_user_box, location_input, risk_badge,
    render_sos_alarm, stop_sos_alarm,
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

# --------------------------------------------------------------------------- #
# PERSISTENT EMERGENCY ALARM
# Rendered on EVERY run while active so the loud siren + repeating
# notifications survive Streamlit reruns. STOP is authoritative.
# --------------------------------------------------------------------------- #
if st.session_state.get("sos_alarm_active"):
    ca, cb = st.columns([4, 1])
    with ca:
        render_sos_alarm(st.session_state.get("sos_alarm_msg",
                                              "Emergency alert is active."))
    with cb:
        st.write("")
        st.write("")
        if st.button("🛑 STOP\nALARM", type="primary", use_container_width=True):
            stop_sos_alarm()
            st.rerun()
    st.divider()

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

force = st.checkbox("Override cooldown (force send)", value=False)

st.markdown("<div class='ws-sos-wrap'>", unsafe_allow_html=True)
trigger = st.button("🚨  TRIGGER SOS  🚨", use_container_width=True,
                    type="primary", disabled=blocked and not force)
st.markdown("</div>", unsafe_allow_html=True)

# --- Handle trigger: create alert, arm alarm, then rerun -------------------
if trigger:
    with st.spinner("Assessing risk, locating you and notifying contacts..."):
        result = alert_service.trigger_sos(
            user, lat, lon, battery_level=battery,
            is_moving=is_moving, force=force,
        )

    if not result["ok"]:
        st.error(result["message"])
    else:
        alert = result["alert"]
        pred = result["prediction"]
        st.session_state["last_alert"] = result
        st.session_state["sos_alarm_active"] = True
        st.session_state["sos_alarm_msg"] = (
            f"{pred['level']} · {alert['address'][:45]} · contacts notified"
        )
        # Rerun so the persistent alarm at the top of the page activates
        st.rerun()

# --- Most-recent alert details (persist across reruns) ---------------------
if st.session_state.get("last_alert"):
    result = st.session_state["last_alert"]
    alert = result["alert"]
    pred = result["prediction"]

    st.success(result["message"])
    risk_badge(pred["level"], pred["score"], pred["confidence"])

    m1, m2, m3 = st.columns(3)
    m1.metric("📍 Address", "Located", alert["address"][:30] + "…")
    m2.metric("🔋 Battery", f"{alert.get('battery_level')}%")
    m3.metric("🏥 Nearest safe place", f"{alert['distance_to_safe_km']} km")

    st.markdown("#### 🛟 Safety recommendations")
    for r in result["recommendations"]:
        st.markdown(f"- {r}")

    st.markdown("#### 📨 Contacts notified")
    if result["notifications"]:
        for n in result["notifications"]:
            icon = "✅" if n["ok"] else "📭"
            st.write(f"{icon} **{n['name']}** — {n['message']}")
    else:
        st.write("No contacts to notify (add trusted contacts to enable).")

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
