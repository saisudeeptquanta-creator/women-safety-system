"""Live map view — current location + alert trail + nearby safe places."""
import streamlit as st
from streamlit_folium import st_folium

from auth import require_login, current_user
from database import get_database
from ui_helpers import load_css, page_header, sidebar_user_box, location_input
import map_service

st.set_page_config(page_title="Live Map", page_icon="🗺️", layout="wide")
load_css()
require_login()
sidebar_user_box()

user = current_user()
db = get_database()
page_header("Live Location Map", "Track your position and nearby safe zones", icon="🗺️")

lat, lon = location_input(key="map")

col1, col2 = st.columns([1, 1])
show_safe = col1.checkbox("Show nearby safe places", value=True)
show_trail = col2.checkbox("Show my recent alert locations", value=True)

# Build map
fmap = map_service.build_map(lat, lon, zoom=14)
map_service.add_user_marker(fmap, lat, lon, popup="Your current location")

# Nearby safe places
if show_safe:
    with st.spinner("Fetching nearby safe places via Overpass API..."):
        places = map_service.find_nearby_places(lat, lon, radius_m=2500)
    map_service.add_place_markers(fmap, places[:25])
    st.caption(f"Found {len(places)} nearby places (police, hospitals, "
               "clinics, bus stations, pharmacies).")

# Alert trail
if show_trail:
    import folium
    history = db.query("LocationHistory", "user_id", user["uid"])
    for _, h in history[-20:]:
        folium.CircleMarker(
            [h["latitude"], h["longitude"]],
            radius=5, color="#d32f2f", fill=True, fill_opacity=0.7,
            popup=f"Alert location · {str(h.get('timestamp',''))[:19]}",
        ).add_to(fmap)

st_folium(fmap, use_container_width=True, height=550)

# Reverse-geocoded address
with st.spinner("Resolving address..."):
    address = map_service.reverse_geocode(lat, lon)
st.info(f"📍 **Current address:** {address}")
