"""
ui_helpers.py
-------------
Shared UI utilities: theme/CSS injection, headers, metric cards,
risk badges and a reusable location-input widget (browser geolocation
component with manual lat/lon fallback).
"""

import os
import streamlit as st
import streamlit.components.v1 as components

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

    Renders the browser-GPS component (streamlit-geolocation) directly so a
    single click reads the device's real coordinates AND writes them straight
    into the latitude/longitude fields. Manual entry/override always works.
    Returns (lat, lon).

    Implementation note: the number_input widgets are bound to session_state
    keys ({key}_lat_in / {key}_lon_in). To programmatically update them from
    the GPS reading we must write to those SAME keys *before* the widgets are
    created and then rerun — otherwise Streamlit keeps the old widget value.
    """
    lat_k, lon_k = f"{key}_lat_in", f"{key}_lon_in"

    # Initialise widget state once
    if lat_k not in st.session_state:
        st.session_state[lat_k] = float(default_lat)
        st.session_state[lon_k] = float(default_lon)

    st.caption("📍 Capture your location")

    # --- Browser GPS component (renders its own clickable location icon) ---
    gps = _read_browser_location(key)
    if gps:
        new_lat, new_lon = round(gps[0], 6), round(gps[1], 6)
        applied = st.session_state.get(f"{key}_gps_applied")
        # Only write + rerun when the reading actually changed (prevents loops)
        if applied != (new_lat, new_lon):
            st.session_state[lat_k] = new_lat
            st.session_state[lon_k] = new_lon
            st.session_state[f"{key}_gps_applied"] = (new_lat, new_lon)
            st.toast(f"📡 GPS locked: {new_lat:.5f}, {new_lon:.5f}", icon="📍")
            st.rerun()
        st.success(f"📡 Live GPS active: {new_lat:.5f}, {new_lon:.5f}")

    # --- Editable fields (now reflect the GPS reading) --------------------
    c1, c2 = st.columns(2)
    with c1:
        lat = st.number_input("Latitude", format="%.6f", key=lat_k)
    with c2:
        lon = st.number_input("Longitude", format="%.6f", key=lon_k)

    # Mirror into convenience keys used elsewhere
    st.session_state[f"{key}_lat"] = lat
    st.session_state[f"{key}_lon"] = lon
    return lat, lon


def _read_browser_location(key):
    """
    Render the streamlit-geolocation component and return (lat, lon) if the
    user has granted access. Returns None when unavailable or not yet shared.
    Click the location 📍 icon and allow the browser permission prompt.
    """
    try:
        from streamlit_geolocation import streamlit_geolocation
    except Exception:
        st.info(
            "Browser GPS component not installed — enter coordinates manually. "
            "Run `pip install streamlit-geolocation` (already in requirements) "
            "and restart the app to enable one-click GPS."
        )
        return None

    st.caption("Tap the location icon and allow access to use real GPS:")
    loc = streamlit_geolocation()
    if loc and loc.get("latitude") is not None and loc.get("longitude") is not None:
        return float(loc["latitude"]), float(loc["longitude"])
    return None


# --------------------------------------------------------------------------- #
# Real-time browser alert: vibration + alarm sound + desktop notification
# --------------------------------------------------------------------------- #
def fire_browser_alert(title="🚨 SOS TRIGGERED", message="Emergency alert sent!"):
    """
    Fire an immediate, real-time alert on the user's own device:
      * navigator.vibrate()  -> phone vibration (mobile browsers)
      * Web Audio beep siren -> audible alarm (no file needed)
      * Notification API      -> desktop/mobile push-style notification
    Injected as a one-shot HTML/JS component so it runs the moment the
    SOS succeeds.
    """
    safe_title = title.replace('"', "'")
    safe_msg = message.replace('"', "'")
    html = f"""
        <script>
        (function() {{
            // 1) Vibrate (mobile) — pattern: buzz, pause, buzz...
            try {{
                if (navigator.vibrate) {{
                    navigator.vibrate([400, 150, 400, 150, 600]);
                }}
            }} catch (e) {{}}

            // 2) Audible siren via Web Audio API (no audio file needed)
            try {{
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                let t = ctx.currentTime;
                for (let i = 0; i < 4; i++) {{
                    const o = ctx.createOscillator();
                    const g = ctx.createGain();
                    o.type = "sine";
                    o.frequency.setValueAtTime(900, t);
                    o.frequency.linearRampToValueAtTime(600, t + 0.35);
                    g.gain.setValueAtTime(0.001, t);
                    g.gain.exponentialRampToValueAtTime(0.5, t + 0.05);
                    g.gain.exponentialRampToValueAtTime(0.001, t + 0.4);
                    o.connect(g); g.connect(ctx.destination);
                    o.start(t); o.stop(t + 0.4);
                    t += 0.5;
                }}
            }} catch (e) {{}}

            // 3) Desktop / mobile notification
            try {{
                function notify() {{
                    new Notification("{safe_title}", {{
                        body: "{safe_msg}",
                        icon: "https://cdn-icons-png.flaticon.com/512/564/564619.png"
                    }});
                }}
                if (window.Notification) {{
                    if (Notification.permission === "granted") {{
                        notify();
                    }} else if (Notification.permission !== "denied") {{
                        Notification.requestPermission().then(function(p) {{
                            if (p === "granted") notify();
                        }});
                    }}
                }}
            }} catch (e) {{}}
        }})();
        </script>
        <div style="font-family:sans-serif;padding:10px 14px;border-radius:10px;
             background:#ffebee;color:#b71c1c;font-weight:700;border-left:5px solid #d32f2f;">
            {safe_title} — {safe_msg}
        </div>
        """
    _render_html(html, height=70)


def _render_html(html, height=70):
    """
    Render an inline HTML/JS snippet in an iframe.

    Prefers the modern ``st.iframe`` (which embeds a raw HTML string via
    srcdoc and runs its scripts) and falls back to the deprecated
    ``components.html`` on older Streamlit versions.
    """
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:  # Streamlit < 1.58 fallback
        components.html(html, height=height)
