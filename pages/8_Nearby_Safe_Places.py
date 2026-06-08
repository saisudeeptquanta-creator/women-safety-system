"""Nearby safe place finder using Overpass + OSRM."""
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

from auth import require_login, current_user
from ui_helpers import load_css, page_header, sidebar_user_box, location_input
import map_service

st.set_page_config(page_title="Safe Places", page_icon="🏥", layout="wide")
load_css()
require_login()
sidebar_user_box()

page_header("Nearby Safe Places", "Police, hospitals, clinics, bus stations & pharmacies", icon="🏥")

lat, lon = location_input(key="safe")

types = st.multiselect(
    "Place types",
    ["police", "hospital", "clinic", "bus_station", "pharmacy"],
    default=["police", "hospital", "bus_station"],
)
radius = st.slider("Search radius (km)", 1, 10, 3) * 1000

if st.button("🔎 Find safe places", use_container_width=True):
    with st.spinner("Querying Overpass API (OpenStreetMap)..."):
        places = map_service.find_nearby_places(
            lat, lon, radius_m=radius, amenities=types or None
        )
    st.session_state["safe_places"] = places

places = st.session_state.get("safe_places", [])

if places:
    fmap = map_service.build_map(lat, lon, zoom=14)
    map_service.add_user_marker(fmap, lat, lon)
    map_service.add_place_markers(fmap, places[:30])

    left, right = st.columns([3, 2])
    with left:
        st_folium(fmap, use_container_width=True, height=480)
    with right:
        st.markdown("#### Closest places")
        df = pd.DataFrame(places)[["name", "type", "distance_km"]].head(15)
        df.columns = ["Name", "Type", "Distance (km)"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        nearest = places[0]
        st.success(f"Nearest: **{nearest['name']}** ({nearest['type']})")
        with st.spinner("Calculating route via OSRM..."):
            dist, dur = map_service.route_distance(
                lat, lon, nearest["lat"], nearest["lon"]
            )
        st.metric("🚶 Route distance", f"{dist} km", f"~{dur} min")
else:
    st.caption("Click **Find safe places** to search around your location.")
