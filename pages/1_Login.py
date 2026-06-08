"""Login page."""
import streamlit as st

from auth import login_user, login_session, is_authenticated, current_user
from ui_helpers import load_css, page_header

st.set_page_config(page_title="Login", page_icon="🔑", layout="centered")
load_css()
page_header("Login", "Access your safety dashboard", icon="🔑")

if is_authenticated():
    st.success(f"Already logged in as {current_user().get('name')}.")
    st.page_link("app.py", label="Go to Home", icon="🏠")
    st.stop()

with st.form("login_form"):
    email = st.text_input("Email", placeholder="you@example.com")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("🔓 Login", use_container_width=True)

if submitted:
    if not email or not password:
        st.warning("Please enter both email and password.")
    else:
        ok, result = login_user(email.strip(), password)
        if ok:
            login_session(result)
            st.success(f"Welcome, {result.get('name')}!")
            st.balloons()
            st.switch_page("app.py")
        else:
            st.error(result)

st.markdown("---")
st.caption("Don't have an account?")
st.page_link("pages/2_Register.py", label="📝 Register here", use_container_width=True)
st.info("Demo admin → **admin@safety.com** / **admin123**")
