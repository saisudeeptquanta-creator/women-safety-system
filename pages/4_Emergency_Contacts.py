"""Emergency contact management."""
import uuid
import streamlit as st

from auth import require_login, current_user
from database import get_database
from ui_helpers import load_css, page_header, sidebar_user_box

st.set_page_config(page_title="Emergency Contacts", page_icon="👥", layout="wide")
load_css()
require_login()
sidebar_user_box()

user = current_user()
db = get_database()
page_header("Emergency Contacts", "People we notify when you trigger an SOS", icon="👥")

# --- Add contact form ------------------------------------------------------
with st.expander("➕ Add a trusted contact", expanded=True):
    with st.form("add_contact"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        relation = c2.text_input("Relation", placeholder="Father / Friend / Sister")
        c3, c4 = st.columns(2)
        phone = c3.text_input("Phone")
        email = c4.text_input("Email")
        submitted = st.form_submit_button("Save contact", use_container_width=True)

    if submitted:
        if not name or not (phone or email):
            st.warning("Provide a name and at least a phone or email.")
        else:
            db.add(
                "EmergencyContacts",
                {
                    "contact_id": str(uuid.uuid4()),
                    "user_id": user["uid"],
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "relation": relation,
                },
            )
            st.success(f"Added {name}.")
            st.rerun()

# --- List contacts ---------------------------------------------------------
st.markdown("### Your contacts")
contacts = db.get_contacts(user["uid"])
if not contacts:
    st.info("No contacts yet. Add at least one so help can reach you.")
else:
    for cid, c in contacts:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 3, 2, 1])
        col1.markdown(f"**{c.get('name')}**")
        col2.write(c.get("relation", "—"))
        col3.write(c.get("email", "—"))
        col4.write(c.get("phone", "—"))
        if col5.button("🗑️", key=f"del_{cid}"):
            db.delete("EmergencyContacts", cid)
            st.rerun()

st.caption(f"Total contacts: {len(contacts)}")
