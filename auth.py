"""
auth.py
-------
Authentication + session management for the Women Safety System.

Uses a self-contained, salted SHA-256 password hashing scheme stored in
the `Users` collection (works in both Firebase and local-JSON modes).
This avoids any paid Firebase Auth dependency while remaining secure for
a project deployment.  Firebase Auth can be layered on later without
changing the calling code.
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone

import streamlit as st

from database import get_database


# --------------------------------------------------------------------------- #
# Password hashing
# --------------------------------------------------------------------------- #
def _hash_password(password: str, salt: str = None):
    salt = salt or uuid.uuid4().hex
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return _hash_password(password, salt) == stored


# --------------------------------------------------------------------------- #
# Registration / login
# --------------------------------------------------------------------------- #
def register_user(name, email, phone, password, role="user"):
    db = get_database()
    uid_existing, _ = db.get_user_by_email(email)
    if uid_existing:
        return False, "An account with this email already exists."

    uid = str(uuid.uuid4())
    user_doc = {
        "uid": uid,
        "name": name,
        "email": email,
        "phone": phone,
        "role": role,
        "password": _hash_password(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.add("Users", user_doc, doc_id=uid)
    return True, uid


def login_user(email, password):
    db = get_database()
    uid, user = db.get_user_by_email(email)
    if not user:
        return False, "No account found for this email."
    if not _verify_password(password, user.get("password", "")):
        return False, "Incorrect password."
    # Store a sanitised user object in session
    safe = {k: v for k, v in user.items() if k != "password"}
    return True, safe


# --------------------------------------------------------------------------- #
# Session helpers
# --------------------------------------------------------------------------- #
def login_session(user_dict):
    st.session_state["authenticated"] = True
    st.session_state["user"] = user_dict


def logout():
    for key in ["authenticated", "user"]:
        st.session_state.pop(key, None)


def current_user():
    return st.session_state.get("user")


def is_authenticated():
    return st.session_state.get("authenticated", False)


def is_admin():
    user = current_user()
    return bool(user and user.get("role") == "admin")


def require_login():
    """Guard placed at the top of every protected page."""
    if not is_authenticated():
        st.warning("🔒 Please log in to access this page.")
        st.page_link("pages/1_Login.py", label="Go to Login", icon="🔑")
        st.stop()


def require_admin():
    require_login()
    if not is_admin():
        st.error("⛔ Admin privileges required to view this page.")
        st.stop()


# --------------------------------------------------------------------------- #
# Bootstrap a default admin so the dashboard is usable out-of-the-box
# --------------------------------------------------------------------------- #
def ensure_default_admin():
    db = get_database()
    uid, _ = db.get_user_by_email("admin@safety.com")
    if not uid:
        register_user(
            name="System Admin",
            email="admin@safety.com",
            phone="0000000000",
            password="admin123",
            role="admin",
        )
