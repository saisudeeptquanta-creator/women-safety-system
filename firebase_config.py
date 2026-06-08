"""
firebase_config.py
------------------
Centralised Firebase Firestore initialisation for the
AI-Powered Smart Women Safety and Emergency Response System.

The module is designed to be FAIL-SAFE:
    * If a valid service-account credential is found, a live Firestore
      client is returned and `FIREBASE_AVAILABLE` is set to True.
    * If Firebase cannot be reached / configured, the rest of the
      application transparently falls back to a local JSON store
      (see database.py).  No feature ever crashes because Firebase
      is missing.

Setup steps are documented in README.md ("Firebase Setup").
"""

import os
import json
import streamlit as st

FIREBASE_AVAILABLE = False
_db_client = None

# Path to a service account JSON file (downloaded from Firebase console).
SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(__file__), "serviceAccountKey.json"
)


def _load_credentials_dict():
    """
    Resolve Firebase credentials from, in priority order:
      1. Streamlit secrets  ([firebase] block in .streamlit/secrets.toml)
      2. Environment variable FIREBASE_CREDENTIALS (raw JSON string)
      3. Local serviceAccountKey.json file
    Returns a dict or None.
    """
    # 1) Streamlit secrets
    try:
        if "firebase" in st.secrets:
            return dict(st.secrets["firebase"])
    except Exception:
        pass

    # 2) Environment variable holding raw JSON
    raw = os.environ.get("FIREBASE_CREDENTIALS")
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass

    # 3) Local file
    if os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            with open(SERVICE_ACCOUNT_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass

    return None


def init_firebase():
    """
    Initialise and cache a Firestore client.
    Returns the client or None (local-fallback mode).
    """
    global FIREBASE_AVAILABLE, _db_client

    if _db_client is not None:
        return _db_client

    creds = _load_credentials_dict()
    if not creds:
        FIREBASE_AVAILABLE = False
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred = credentials.Certificate(creds)
            firebase_admin.initialize_app(cred)

        _db_client = firestore.client()
        FIREBASE_AVAILABLE = True
        return _db_client
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[firebase_config] Firebase init failed -> local mode: {exc}")
        FIREBASE_AVAILABLE = False
        return None


def get_db():
    """Public accessor used by database.py."""
    return init_firebase()
