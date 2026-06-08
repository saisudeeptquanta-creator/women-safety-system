"""Registration page."""
import streamlit as st

from auth import register_user, login_user, login_session
from ui_helpers import load_css, page_header

st.set_page_config(page_title="Register", page_icon="📝", layout="centered")
load_css()
page_header("Create Account", "Join the safety network", icon="📝")

with st.form("register_form"):
    name = st.text_input("Full name")
    email = st.text_input("Email")
    phone = st.text_input("Phone number")
    col1, col2 = st.columns(2)
    password = col1.text_input("Password", type="password")
    confirm = col2.text_input("Confirm password", type="password")
    role = st.selectbox("Account type", ["user", "admin"], index=0)
    submitted = st.form_submit_button("✅ Register", use_container_width=True)

if submitted:
    if not all([name, email, phone, password]):
        st.warning("Please fill in all fields.")
    elif password != confirm:
        st.error("Passwords do not match.")
    elif len(password) < 6:
        st.error("Password must be at least 6 characters.")
    else:
        ok, result = register_user(name.strip(), email.strip(),
                                   phone.strip(), password, role)
        if ok:
            st.success("Account created! Logging you in...")
            _, user = login_user(email.strip(), password)
            login_session(user)
            st.balloons()
            st.switch_page("app.py")
        else:
            st.error(result)

st.markdown("---")
st.page_link("pages/1_Login.py", label="🔑 Already registered? Login", use_container_width=True)
