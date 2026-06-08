"""Emergency contact management + phone-alert (Telegram) setup."""
import uuid
import streamlit as st

from auth import require_login, current_user
from database import get_database
from ui_helpers import load_css, page_header, sidebar_user_box
import notification_service

st.set_page_config(page_title="Emergency Contacts", page_icon="👥", layout="wide")
load_css()
require_login()
sidebar_user_box()

user = current_user()
db = get_database()
page_header("Emergency Contacts", "People we notify when you trigger an SOS", icon="👥")

# =========================================================================== #
# PHONE ALERTS (reach you even when the app/browser is CLOSED)
# =========================================================================== #
with st.container(border=True):
    st.markdown("### 📲 Phone alerts — get notified even when the app is closed")

    tg_ok, _ = notification_service.channels_status()[0]
    sms_ok = notification_service.twilio_configured()

    s1, s2 = st.columns(2)
    s1.write(("🟢" if tg_ok else "🔴") + " **Telegram push** "
             + ("active (free)" if tg_ok else "not configured"))
    s2.write(("🟢" if sms_ok else "⚪") + " **SMS / Call** "
             + ("active" if sms_ok else "optional (Twilio)"))

    if not tg_ok:
        st.info(
            "**Enable free background phone alerts in 3 steps:**\n"
            "1. In Telegram, open **@BotFather** → `/newbot` → copy the **bot token**.\n"
            "2. Add the token to the app **Secrets** under `[telegram] bot_token`.\n"
            "3. Open your new bot, tap **Start**, then get your **chat ID** from "
            "**@userinfobot** and paste it below.\n\n"
            "Once set, your phone's Telegram app rings/notifies you even with the "
            "browser fully closed."
        )

    # --- Save MY own Telegram chat id (self-alert to my phone) ----
    current_chat = user.get("telegram_chat_id", "")
    cc1, cc2 = st.columns([3, 1])
    my_chat = cc1.text_input("My Telegram chat ID (alerts to my own phone)",
                             value=current_chat, key="my_tg",
                             placeholder="e.g. 123456789")
    cc2.write("")
    cc2.write("")
    if cc2.button("💾 Save my ID", use_container_width=True):
        db.update("Users", user["uid"], {"telegram_chat_id": my_chat.strip()})
        st.session_state["user"]["telegram_chat_id"] = my_chat.strip()
        st.success("Saved. Your phone will be alerted on SOS.")
        st.rerun()

    if current_chat:
        if st.button("🔔 Send test alert to my phone now"):
            ok, msg = notification_service.send_telegram(
                current_chat,
                "✅ Test alert from your Women Safety System. "
                "If you see this with the browser closed, phone alerts work!",
            )
            (st.success if ok else st.error)(msg)

# --- Add contact form ------------------------------------------------------
with st.expander("➕ Add a trusted contact", expanded=True):
    with st.form("add_contact"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        relation = c2.text_input("Relation", placeholder="Father / Friend / Sister")
        c3, c4 = st.columns(2)
        phone = c3.text_input("Phone (for SMS / call)")
        email = c4.text_input("Email")
        tg = st.text_input("Contact's Telegram chat ID (optional, for phone push)",
                           placeholder="They start your bot, then share their @userinfobot ID")
        submitted = st.form_submit_button("Save contact", use_container_width=True)

    if submitted:
        if not name or not (phone or email or tg):
            st.warning("Provide a name and at least a phone, email or Telegram ID.")
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
                    "telegram_chat_id": tg.strip(),
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
        col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 3, 2, 2, 1])
        col1.markdown(f"**{c.get('name')}**")
        col2.write(c.get("relation", "—"))
        col3.write(c.get("email", "—"))
        col4.write(c.get("phone", "—"))
        col5.write("📲 " + ("TG ✓" if c.get("telegram_chat_id") else "—"))
        if col6.button("🗑️", key=f"del_{cid}"):
            db.delete("EmergencyContacts", cid)
            st.rerun()

st.caption(f"Total contacts: {len(contacts)}")
