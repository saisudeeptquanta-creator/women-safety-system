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
# Real-time EMERGENCY ALARM:
#   * Continuous, loud, wailing two-tone siren (loops until stopped)
#   * Repeating phone vibration
#   * Repeating desktop/mobile notification popups (stay on screen)
#   * Flashing full-width banner with ACTIVATE / STOP controls
# --------------------------------------------------------------------------- #
# The siren markup/JS is kept as a token template (not an f-string) to avoid
# brace-escaping problems with the large amount of inline JavaScript.
_ALARM_TEMPLATE = r"""
<style>
  @keyframes sosflash { 0%{background:#d32f2f} 50%{background:#6a0000} 100%{background:#d32f2f} }
  .sos-wrap{font-family:'Segoe UI',sans-serif;color:#fff;border-radius:16px;
            padding:18px 16px;text-align:center;animation:sosflash .7s infinite;
            box-shadow:0 8px 26px rgba(211,47,47,.45);}
  .sos-title{font-size:24px;font-weight:900;letter-spacing:.5px;}
  .sos-msg{font-size:15px;margin:6px 0 12px;opacity:.95;}
  .sos-btn{font-size:17px;font-weight:800;border:none;border-radius:12px;
           padding:13px 22px;margin:5px;cursor:pointer;}
  #sosArm{background:#ffffff;color:#b71c1c;}
  #sosStop{background:#111;color:#fff;}
  #sosStatus{margin-top:8px;font-size:13px;min-height:16px;}
</style>
<div class="sos-wrap">
  <div class="sos-title">🚨 EMERGENCY SOS ACTIVE 🚨</div>
  <div class="sos-msg">__MESSAGE__</div>
  <button id="sosArm" class="sos-btn">🔊 ACTIVATE LOUD SIREN</button>
  <button id="sosStop" class="sos-btn">🛑 STOP ALARM</button>
  <div id="sosStatus">Starting alarm…</div>
</div>
<script>
(function() {
  var ctx=null, osc=null, master=null;
  var sirenInt=null, vibInt=null, notifInt=null, high=true, running=false;

  function sweep(){
    if(!ctx||!osc) return;
    var now=ctx.currentTime;
    try{ osc.frequency.cancelScheduledValues(now); }catch(e){}
    if(high){ osc.frequency.setValueAtTime(740, now);
              osc.frequency.linearRampToValueAtTime(1500, now+0.55); }
    else    { osc.frequency.setValueAtTime(1500, now);
              osc.frequency.linearRampToValueAtTime(740, now+0.55); }
    high=!high;
  }

  function setStatus(){
    var el=document.getElementById('sosStatus'); if(!el) return;
    if(ctx && ctx.state==='running' && running){
      el.innerText='🔊 Siren wailing — tap STOP when safe.';
    } else {
      el.innerText='⚠️ Tap "🔊 ACTIVATE LOUD SIREN" to start the alarm sound.';
    }
  }

  function ensureCtx(){
    if(ctx) return;
    ctx = new (window.AudioContext||window.webkitAudioContext)();
    master = ctx.createGain(); master.gain.value=0.0001;
    master.connect(ctx.destination);
    osc = ctx.createOscillator(); osc.type='sawtooth';
    osc.connect(master); osc.start();
  }

  function startAudio(){
    try{
      ensureCtx();
      // Browsers often start the context suspended (autoplay policy):
      // resuming requires a user gesture, which the ACTIVATE/STOP taps provide.
      if(ctx.state==='suspended'){ ctx.resume().then(setStatus); }
      if(!running){
        master.gain.exponentialRampToValueAtTime(0.85, ctx.currentTime+0.15); // LOUD
        sweep(); sirenInt=setInterval(sweep, 550);
        running=true;
      }
      setStatus();
    }catch(e){ setStatus(); }
  }

  function startVibration(){
    if(vibInt) return;
    function buzz(){ try{ if(navigator.vibrate) navigator.vibrate([700,250,700]); }catch(e){} }
    buzz(); vibInt=setInterval(buzz, 1700);
  }

  function fireNotif(){
    try{
      if(window.Notification && Notification.permission==='granted'){
        new Notification("🚨 SOS EMERGENCY", {
          body:"__MESSAGE__",
          requireInteraction:true, renotify:true, tag:'sos-alert',
          icon:"https://cdn-icons-png.flaticon.com/512/564/564619.png"
        });
      }
    }catch(e){}
  }
  function startNotifications(){
    if(notifInt) return;
    function go(){ fireNotif(); }
    if(window.Notification){
      if(Notification.permission==='granted'){ go(); }
      else if(Notification.permission!=='denied'){
        Notification.requestPermission().then(function(p){ if(p==='granted') go(); });
      }
    }
    notifInt=setInterval(fireNotif, 5000); // repeating real-time popups
  }

  function startAll(){ startAudio(); startVibration(); startNotifications(); }

  function stopAll(){
    try{ if(sirenInt) clearInterval(sirenInt);
         if(master&&ctx){ master.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime+0.2); }
         if(osc) osc.stop(ctx.currentTime+0.3); }catch(e){}
    if(vibInt){ clearInterval(vibInt); vibInt=null; }
    if(notifInt){ clearInterval(notifInt); notifInt=null; }
    try{ if(navigator.vibrate) navigator.vibrate(0); }catch(e){}
    running=false;
    document.getElementById('sosStatus').innerText='✅ Alarm stopped.';
  }

  document.getElementById('sosArm').addEventListener('click', startAll);
  document.getElementById('sosStop').addEventListener('click', stopAll);
  // Any tap inside the frame also arms/resumes audio (autoplay restrictions)
  document.body.addEventListener('click', function(){ startAudio(); }, {once:false});

  // Attempt to auto-start immediately (works when the browser allows it)
  startVibration(); startNotifications(); startAudio();
})();
</script>
"""


def render_sos_alarm(message="Emergency alert sent — help is being notified."):
    """
    Render the persistent, loud, continuous emergency alarm. Call this on
    every run while ``st.session_state['sos_alarm_active']`` is True so the
    siren survives Streamlit reruns. Use ``stop_sos_alarm()`` to clear it.
    """
    safe_msg = message.replace('"', "'").replace("<", "").replace(">", "")
    html = _ALARM_TEMPLATE.replace("__MESSAGE__", safe_msg)
    _render_html(html, height=210)


def stop_sos_alarm():
    """Authoritative stop: clears the alarm flag so the iframe is removed."""
    st.session_state["sos_alarm_active"] = False


# Backwards-compatible one-shot helper (kept so existing imports keep working)
def fire_browser_alert(title="🚨 SOS TRIGGERED", message="Emergency alert sent!"):
    render_sos_alarm(message)


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
