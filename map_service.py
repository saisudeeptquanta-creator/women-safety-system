"""
map_service.py
--------------
Location intelligence powered exclusively by FREE / open APIs:

    * Nominatim (OpenStreetMap)  -> reverse geocoding lat/lon -> address
    * Overpass API               -> nearby police, hospitals, clinics,
                                     bus stations, pharmacies, safe places
    * OSRM public server         -> driving route distance / duration
    * Haversine formula          -> instant local distance fallback

All network calls are wrapped defensively: if an API is unreachable the
function returns a sensible fallback so the app never breaks offline.
"""

import math
import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

HEADERS = {"User-Agent": "WomenSafetySystem/1.0 (educational-project)"}

# Map our friendly names -> OSM amenity tags
AMENITY_TAGS = {
    "police": "police",
    "hospital": "hospital",
    "clinic": "clinic",
    "bus_station": "bus_station",
    "pharmacy": "pharmacy",
}

ICON_MAP = {
    "police": ("blue", "shield"),
    "hospital": ("red", "plus-square"),
    "clinic": ("orange", "plus"),
    "bus_station": ("green", "bus"),
    "pharmacy": ("purple", "medkit"),
}


# --------------------------------------------------------------------------- #
# Distance
# --------------------------------------------------------------------------- #
def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


# --------------------------------------------------------------------------- #
# Reverse geocoding (Nominatim)
# --------------------------------------------------------------------------- #
def reverse_geocode(lat, lon):
    """Return a human-readable address for a coordinate."""
    try:
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 18}
        resp = requests.get(
            NOMINATIM_URL, params=params, headers=HEADERS, timeout=10
        )
        if resp.ok:
            data = resp.json()
            return data.get("display_name", f"{lat:.5f}, {lon:.5f}")
    except Exception:
        pass
    return f"Lat {lat:.5f}, Lon {lon:.5f}"


# --------------------------------------------------------------------------- #
# Nearby places (Overpass)
# --------------------------------------------------------------------------- #
def _build_overpass_query(lat, lon, radius_m, amenities):
    parts = []
    for amen in amenities:
        tag = AMENITY_TAGS.get(amen, amen)
        parts.append(f'node["amenity"="{tag}"](around:{radius_m},{lat},{lon});')
        parts.append(f'way["amenity"="{tag}"](around:{radius_m},{lat},{lon});')
    body = "".join(parts)
    return f"[out:json][timeout:25];({body});out center 40;"


def find_nearby_places(lat, lon, radius_m=3000, amenities=None):
    """
    Query Overpass for safe places near a coordinate.
    Returns a list of dicts: name, type, lat, lon, distance_km.
    """
    amenities = amenities or list(AMENITY_TAGS.keys())
    query = _build_overpass_query(lat, lon, radius_m, amenities)
    places = []
    try:
        resp = requests.post(
            OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=30
        )
        if resp.ok:
            for el in resp.json().get("elements", []):
                if el["type"] == "node":
                    plat, plon = el.get("lat"), el.get("lon")
                else:  # way -> use center
                    center = el.get("center", {})
                    plat, plon = center.get("lat"), center.get("lon")
                if plat is None or plon is None:
                    continue
                tags = el.get("tags", {})
                places.append(
                    {
                        "name": tags.get("name", tags.get("amenity", "Unnamed").title()),
                        "type": tags.get("amenity", "place"),
                        "lat": plat,
                        "lon": plon,
                        "distance_km": round(haversine(lat, lon, plat, plon), 2),
                    }
                )
    except Exception:
        pass

    places.sort(key=lambda p: p["distance_km"])
    return places


def nearest_safe_place(lat, lon, radius_m=5000):
    """Return the single closest safe place (or None)."""
    places = find_nearby_places(
        lat, lon, radius_m, amenities=["police", "hospital"]
    )
    return places[0] if places else None


# --------------------------------------------------------------------------- #
# Route distance (OSRM)
# --------------------------------------------------------------------------- #
def route_distance(lat1, lon1, lat2, lon2):
    """
    Return (distance_km, duration_min) using the free OSRM server.
    Falls back to Haversine distance with an estimated walking time.
    """
    try:
        url = f"{OSRM_URL}/{lon1},{lat1};{lon2},{lat2}"
        resp = requests.get(
            url, params={"overview": "false"}, headers=HEADERS, timeout=10
        )
        if resp.ok:
            data = resp.json()
            if data.get("routes"):
                route = data["routes"][0]
                return (
                    round(route["distance"] / 1000.0, 2),
                    round(route["duration"] / 60.0, 1),
                )
    except Exception:
        pass

    dist = haversine(lat1, lon1, lat2, lon2)
    return round(dist, 2), round(dist / 5 * 60, 1)  # ~5 km/h walking


# --------------------------------------------------------------------------- #
# Folium helpers
# --------------------------------------------------------------------------- #
def build_map(center_lat, center_lon, zoom=14):
    """Create a base Folium map using OpenStreetMap tiles."""
    import folium

    return folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="OpenStreetMap",
        control_scale=True,
    )


def add_user_marker(fmap, lat, lon, popup="Your location"):
    import folium

    folium.Marker(
        [lat, lon],
        popup=popup,
        tooltip="You are here",
        icon=folium.Icon(color="darkpurple", icon="user", prefix="fa"),
    ).add_to(fmap)
    folium.Circle(
        [lat, lon], radius=120, color="#7b2ff7", fill=True, fill_opacity=0.15
    ).add_to(fmap)
    return fmap


def add_place_markers(fmap, places):
    import folium

    for p in places:
        color, icon = ICON_MAP.get(p["type"], ("gray", "info-sign"))
        folium.Marker(
            [p["lat"], p["lon"]],
            popup=f"{p['name']} ({p['type']}) — {p['distance_km']} km",
            tooltip=p["name"],
            icon=folium.Icon(color=color, icon=icon, prefix="fa"),
        ).add_to(fmap)
    return fmap
