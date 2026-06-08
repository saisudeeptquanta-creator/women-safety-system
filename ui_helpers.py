"""
ui_helpers.py
-------------
Shared UI utilities: theme/CSS injection, headers, metric cards,
risk badges and a reusable location-input widget (browser geolocation
component with manual lat/lon fallback).
"""

import os
import streamlit as st

ASSETS = os.path.join(os.path.dirname(__file__), "assets")


def load_css():
    """Inject the global stylesheet + a few inline polish rules."""
    css_path = os.path.join(ASSETS, "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as fh:
            st.markdown(f"<style>{fh.read()}</style>", unsafe_allow_html=True)


def page_header(title, subtitle="", icon="🛡️"):
    st.markdown(
        f"""
        <div class="ws-header">
            <div class="ws-header-icon">{icon}</div>
            <div>
                <div class="ws-header-title">{title}</div>
                <div class="ws-header-sub">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value, icon="📊", color="#7b2ff7"):
    st.markdown(
        f"""
        <div class="ws-metric" style="border-left:5px solid {color}">
            <div class="ws-metric-icon">{icon}</div>
            <div class="ws-metric-value">{value}</div>
            <div class="ws-metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_badge(level, score=None, confidence=None):
    colors = {
        "Low Risk": "#1faa59",
        "Medium Risk": "#f4b400",
        "High Risk": "#ff7043",
        "Critical Risk": "#d32f2f",
    }
    color = colors.get(level, "#7b2ff7")
    extra = ""
    if score is not None:
        extra += f" &nbsp;|&nbsp; Score {score}"
    if confidence is not None:
        extra += f" &nbsp;|&nbsp; Confidence {confidence}%"
    st.markdown(
        f"""
        <div class="ws-risk-badge" style="background:{color}">
            {level}{extra}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_user_box():
    from auth import current_user, logout

    user = current_user()
    if not user:
        return
    role = user.get("role", "user").title()
    st.sidebar.markdown(
        f"""
        <div class="ws-user-box">
            <div class="ws-avatar">{user.get('name', 'U')[0].upper()}</div>
            <div>
                <div class="ws-user-name">{user.get('name')}</div>
                <div class="ws-user-role">{role}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()


def location_input(default_lat=17.3850, default_lon=78.4867, key="loc"):
    """
    Reusable location capture widget.

    Tries the browser geolocation via streamlit-geolocation if installed,
    otherwise offers manual latitude/longitude entry with sensible
    defaults (Hyderabad city centre).  Returns (lat, lon).
    """
    lat = st.session_state.get(f"{key}_lat", default_lat)
    lon = st.session_state.get(f"{key}_lon", default_lon)

    st.caption("📍 Capture your location")
    cols = st.columns([1, 1, 1])

    with cols[0]:
        lat = st.number_input("Latitude", value=float(lat), format="%.6f",
                              key=f"{key}_lat_in")
    with cols[1]:
        lon = st.number_input("Longitude", value=float(lon), format="%.6f",
                              key=f"{key}_lon_in")
    with cols[2]:
        st.write("")
        st.write("")
        if st.button("🔄 Use browser GPS", key=f"{key}_gps"):
            _try_browser_location(key)

    # If a browser location was captured, prefer it
    if st.session_state.get(f"{key}_gps_lat"):
        lat = st.session_state[f"{key}_gps_lat"]
        lon = st.session_state[f"{key}_gps_lon"]
        st.success(f"Browser location: {lat:.5f}, {lon:.5f}")

    st.session_state[f"{key}_lat"] = lat
    st.session_state[f"{key}_lon"] = lon
    return lat, lon


def _try_browser_location(key):
    """Attempt to read browser GPS via the optional streamlit-geolocation."""
    try:
        from streamlit_geolocation import streamlit_geolocation

        loc = streamlit_geolocation()
        if loc and loc.get("latitude"):
            st.session_state[f"{key}_gps_lat"] = loc["latitude"]
            st.session_state[f"{key}_gps_lon"] = loc["longitude"]
    except Exception:
        st.info(
            "Browser GPS component not installed — enter coordinates "
            "manually. (pip install streamlit-geolocation to enable.)"
        )
