"""
app.py  —  Application entry point (Home page)
==============================================
AI-Powered Smart Women Safety and Emergency Response System
Using Streamlit, Firebase, Real-Time Location Tracking, and
Intelligent Risk Prediction.

Run with:
    streamlit run app.py
"""

import streamlit as st

from auth import (
    ensure_default_admin,
    is_authenticated,
    current_user,
)
from database import get_database
from ui_helpers import load_css, page_header, metric_card, sidebar_user_box

st.set_page_config(
    page_title="Smart Women Safety System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

# Bootstrap default admin + attempt to sync any locally buffered alerts
ensure_default_admin()
db = get_database()
synced = db.sync_pending()

# ---------------------------------------------------------------- Sidebar
with st.sidebar:
    st.markdown("## 🛡️ Safety System")
    st.caption(f"Data backend: **{db.status()}**")
    if synced:
        st.success(f"Synced {synced} offline record(s) to Firebase.")
    if is_authenticated():
        sidebar_user_box()
    else:
        st.info("Login or register to access all features.")
        st.page_link("pages/1_Login.py", label="Login", icon="🔑")
        st.page_link("pages/2_Register.py", label="Register", icon="📝")

# ---------------------------------------------------------------- Hero
page_header(
    "AI-Powered Smart Women Safety System",
    "Real-time SOS alerts · Intelligent risk prediction · Location intelligence",
    icon="🛡️",
)

user = current_user()
if user:
    st.success(f"Welcome back, **{user.get('name')}** 👋")
    c1, c2, c3, c4 = st.columns(4)
    alerts = db.get_user_alerts(user["uid"])
    active = sum(1 for _, a in alerts if a.get("status") == "Active")
    contacts = db.get_contacts(user["uid"])
    with c1:
        metric_card("My Alerts", len(alerts), "🚨", "#d32f2f")
    with c2:
        metric_card("Active Alerts", active, "🟠", "#ff7043")
    with c3:
        metric_card("Trusted Contacts", len(contacts), "👥", "#1faa59")
    with c4:
        metric_card("Backend", "Online" if db.online else "Local", "💾", "#7b2ff7")

    st.markdown("### Quick actions")
    q1, q2, q3, q4 = st.columns(4)
    q1.page_link("pages/5_SOS_Alert.py", label="🚨 Trigger SOS", use_container_width=True)
    q2.page_link("pages/6_Live_Map.py", label="🗺️ Live Map", use_container_width=True)
    q3.page_link("pages/8_Nearby_Safe_Places.py", label="🏥 Safe Places", use_container_width=True)
    q4.page_link("pages/9_AI_Risk_Prediction.py", label="🤖 Risk AI", use_container_width=True)
else:
    st.markdown(
        """
        ### Your personal safety companion 💜

        This platform combines **artificial intelligence**, **real-time location
        tracking**, and **open mapping data** to keep users safe and to help
        responders act fast.
        """
    )

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("#### 🚨 One-click SOS")
        st.write(
            "Instantly alert trusted contacts with your live location, "
            "address, battery level and an AI-computed risk score."
        )
    with f2:
        st.markdown("#### 🤖 AI Risk Prediction")
        st.write(
            "A Random Forest model analyses time, location, battery, and "
            "history to classify risk as Low, Medium, High or Critical."
        )
    with f3:
        st.markdown("#### 🗺️ Location Intelligence")
        st.write(
            "Find nearby police stations, hospitals and safe zones using "
            "free OpenStreetMap, Nominatim, Overpass and OSRM APIs."
        )

    st.markdown("---")
    st.markdown("#### Get started")
    g1, g2 = st.columns(2)
    g1.page_link("pages/2_Register.py", label="📝 Create an account", use_container_width=True)
    g2.page_link("pages/1_Login.py", label="🔑 Login", use_container_width=True)

    st.info("Demo admin login → **admin@safety.com** / **admin123**")

st.markdown(
    "<div class='ws-footer'>Major Project · AI-Powered Smart Women Safety "
    "& Emergency Response System</div>",
    unsafe_allow_html=True,
)
