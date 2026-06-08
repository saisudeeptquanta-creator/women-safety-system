"""
database.py
-----------
Unified data-access layer for the Women Safety System.

Provides a single API (DB) that talks to Firebase Firestore when it is
available and transparently falls back to a local JSON document store
otherwise.  It also supports SYNCING locally-buffered records up to
Firestore once connectivity is restored.

Collections handled:
    Users, EmergencyContacts, Alerts, LocationHistory,
    SafePlaces, Reports

Every public method works identically in both modes so that the rest of
the application never needs to know where the data physically lives.
"""

import os
import json
import uuid
import threading
from datetime import datetime, timezone

from firebase_config import get_db, FIREBASE_AVAILABLE
import firebase_config

# --------------------------------------------------------------------------- #
# Local JSON store configuration
# --------------------------------------------------------------------------- #
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "local_store")
os.makedirs(DATA_DIR, exist_ok=True)

COLLECTIONS = [
    "Users",
    "EmergencyContacts",
    "Alerts",
    "LocationHistory",
    "SafePlaces",
    "Reports",
]

_lock = threading.Lock()


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _local_path(collection):
    return os.path.join(DATA_DIR, f"{collection}.json")


def _read_local(collection):
    path = _local_path(collection)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _write_local(collection, data):
    path = _local_path(collection)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)


class Database:
    """High-level CRUD wrapper used across the whole application."""

    def __init__(self):
        self.client = get_db()

    # ------------------------------------------------------------------ #
    # Status helpers
    # ------------------------------------------------------------------ #
    @property
    def online(self):
        return firebase_config.FIREBASE_AVAILABLE and self.client is not None

    def status(self):
        return "Firebase (online)" if self.online else "Local JSON (offline)"

    # ------------------------------------------------------------------ #
    # Generic create / read / update
    # ------------------------------------------------------------------ #
    def add(self, collection, doc, doc_id=None):
        """Insert a document and return its id."""
        doc_id = doc_id or str(uuid.uuid4())
        doc = dict(doc)
        doc.setdefault("created_at", _now_iso())

        if self.online:
            try:
                self.client.collection(collection).document(doc_id).set(doc)
                return doc_id
            except Exception as exc:
                print(f"[database] Firestore add failed, buffering locally: {exc}")

        # local fallback
        with _lock:
            data = _read_local(collection)
            doc["_pending_sync"] = not self.online
            data[doc_id] = doc
            _write_local(collection, data)
        return doc_id

    def get(self, collection, doc_id):
        if self.online:
            try:
                snap = self.client.collection(collection).document(doc_id).get()
                return snap.to_dict() if snap.exists else None
            except Exception:
                pass
        return _read_local(collection).get(doc_id)

    def update(self, collection, doc_id, updates):
        updates = dict(updates)
        if self.online:
            try:
                self.client.collection(collection).document(doc_id).update(updates)
                return True
            except Exception:
                pass
        with _lock:
            data = _read_local(collection)
            if doc_id in data:
                data[doc_id].update(updates)
                _write_local(collection, data)
                return True
        return False

    def delete(self, collection, doc_id):
        if self.online:
            try:
                self.client.collection(collection).document(doc_id).delete()
                return True
            except Exception:
                pass
        with _lock:
            data = _read_local(collection)
            if doc_id in data:
                del data[doc_id]
                _write_local(collection, data)
                return True
        return False

    def all(self, collection):
        """Return list of (id, doc) for an entire collection."""
        if self.online:
            try:
                return [
                    (d.id, d.to_dict())
                    for d in self.client.collection(collection).stream()
                ]
            except Exception:
                pass
        return list(_read_local(collection).items())

    def query(self, collection, field, value):
        """Simple equality filter."""
        results = []
        if self.online:
            try:
                docs = (
                    self.client.collection(collection)
                    .where(field, "==", value)
                    .stream()
                )
                return [(d.id, d.to_dict()) for d in docs]
            except Exception:
                pass
        for doc_id, doc in _read_local(collection).items():
            if doc.get(field) == value:
                results.append((doc_id, doc))
        return results

    # ------------------------------------------------------------------ #
    # Offline -> online synchronisation
    # ------------------------------------------------------------------ #
    def sync_pending(self):
        """
        Push every locally buffered (_pending_sync=True) record up to
        Firestore once it is reachable again. Returns number synced.
        """
        if not self.online:
            return 0
        synced = 0
        for collection in COLLECTIONS:
            data = _read_local(collection)
            changed = False
            for doc_id, doc in list(data.items()):
                if doc.get("_pending_sync"):
                    try:
                        clean = {k: v for k, v in doc.items() if k != "_pending_sync"}
                        self.client.collection(collection).document(doc_id).set(clean)
                        doc["_pending_sync"] = False
                        synced += 1
                        changed = True
                    except Exception:
                        pass
            if changed:
                _write_local(collection, data)
        return synced

    # ------------------------------------------------------------------ #
    # Domain-specific convenience helpers
    # ------------------------------------------------------------------ #
    # Users
    def get_user_by_email(self, email):
        for uid, doc in self.all("Users"):
            if doc.get("email", "").lower() == email.lower():
                return uid, doc
        return None, None

    def get_contacts(self, user_id):
        return self.query("EmergencyContacts", "user_id", user_id)

    def get_user_alerts(self, user_id):
        alerts = self.query("Alerts", "user_id", user_id)
        return sorted(
            alerts, key=lambda x: x[1].get("created_at", ""), reverse=True
        )

    def get_all_alerts(self):
        alerts = self.all("Alerts")
        return sorted(
            alerts, key=lambda x: x[1].get("created_at", ""), reverse=True
        )


# Singleton accessor ---------------------------------------------------------
_db_instance = None


def get_database():
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
