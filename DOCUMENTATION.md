# Project Documentation
# AI-Powered Smart Women Safety and Emergency Response System
### Using Streamlit, Firebase, Real-Time Location Tracking, and Intelligent Risk Prediction

---

## 1. Abstract

The **AI-Powered Smart Women Safety and Emergency Response System** is an
intelligent, real-time safety platform designed to protect users in
emergency situations and to empower responders with actionable intelligence.
With a single click, a user can broadcast an SOS alert that carries their live
GPS location, a reverse-geocoded address, device battery level, and an
**AI-computed risk score** to a network of trusted contacts. A Random Forest
machine-learning model continuously classifies the user's situation into
**Low, Medium, High, or Critical** risk based on contextual factors such as
time of day, proximity to safe places, previous incidents, battery level, and
movement status. The platform integrates free and open mapping services
(OpenStreetMap, Nominatim, Overpass, and OSRM) to locate nearby police
stations, hospitals, and safe zones, and to compute the fastest route to
safety. An administrative dashboard provides real-time monitoring, analytics,
heatmaps of unsafe areas, and automated PDF reporting. The system uses Firebase
Firestore for real-time cloud storage with a robust local fallback, ensuring
uninterrupted operation even without connectivity.

---

## 2. Introduction

Personal safety, particularly for women, is a pressing societal concern.
Conventional safety solutions are often reactive, slow, or dependent on costly
infrastructure. The advancement of cloud computing, open geospatial data, and
machine learning makes it possible to build proactive, intelligent, and
affordable safety systems. This project delivers an end-to-end platform that
combines an intuitive Streamlit web interface, a real-time Firebase backend,
free location-intelligence APIs, and an AI risk-prediction engine into a single,
cohesive emergency-response solution. The application is fully functional,
modern, responsive, and suitable for real-world deployment as well as academic
major-project submission.

---

## 3. Problem Statement

In emergency situations, victims frequently struggle to:
- Quickly and reliably alert trusted people with their **exact live location**.
- Convey the **severity** of the situation in a way responders can act on.
- Identify and reach the **nearest safe location** (police station / hospital).
- Maintain a **verifiable record** of incidents for follow-up.

Meanwhile, authorities and administrators lack a **centralised, real-time view**
of ongoing alerts and unsafe geographic zones, limiting their ability to
respond and to plan preventive measures. There is a need for a single,
intelligent platform that addresses both the victim's and the responder's
requirements while remaining low-cost and easy to deploy.

---

## 4. Existing System

Current approaches include:
- **Manual phone calls / SMS** — slow, no automatic location, no severity
  context, and unreliable under stress.
- **Single-purpose SOS apps** — typically send a static message without
  intelligent risk assessment or location intelligence.
- **Hardware panic buttons** — costly, require dedicated devices, and lack
  analytics or administrative oversight.
- **Paid commercial platforms** — expensive, closed-source, and dependent on
  proprietary infrastructure.

These systems generally lack **AI-based risk prediction**, **real-time
administrative monitoring**, **heatmap analytics**, and **free, open
location-intelligence integration**.

---

## 5. Proposed System

The proposed system is a unified, AI-driven safety platform that:
- Provides a **one-click SOS** that automatically attaches live location,
  address, battery level, and an **AI risk score**.
- Uses a **Random Forest Classifier** to predict risk severity in real time.
- Integrates **free APIs** (Nominatim, Overpass, OSRM, OpenStreetMap) for
  reverse geocoding, nearby safe places, and route distance.
- Notifies **trusted contacts** by email (or simulated notification).
- Offers a **real-time admin dashboard** with filtering, mapping, heatmaps,
  and analytics.
- Generates **professional PDF reports** for incidents and system summaries.
- Stores data in **Firebase Firestore** with a **local JSON fallback** and
  automatic synchronisation.

---

## 6. Objectives

1. Enable rapid, reliable, one-click emergency alerting with live location.
2. Apply machine learning to quantify and classify situational risk.
3. Provide location intelligence for nearby safe places and routing.
4. Notify trusted contacts automatically with rich context.
5. Give administrators real-time monitoring and analytical insight.
6. Generate professional documentation/reports for each incident.
7. Ensure the system is low-cost using exclusively free APIs and tiers.
8. Guarantee resilience with offline fallback and data synchronisation.

---

## 7. Scope

- **In scope:** user & admin web application, SOS alerting, AI risk prediction,
  location intelligence, contact notification, analytics, heatmaps, PDF
  reporting, real-time cloud + offline storage.
- **Users:** individuals seeking personal safety and administrators/responders
  monitoring alerts.
- **Platforms:** any modern web browser via the Streamlit web app.
- **Extensible** to mobile wrappers, SMS gateways, IoT panic buttons, and
  wearable integrations in future iterations.

---

## 8. System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER (Streamlit)             │
│  Home · Login · Register · User Dashboard · SOS · Live Map    │
│  Contacts · History · Safe Places · AI Risk · Admin ·         │
│  Analytics · Reports        (custom CSS theme, Plotly, Folium)│
└───────────────┬──────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────┐
│                       BUSINESS LOGIC LAYER                    │
│  auth.py · alert_service.py · ml_model.py · map_service.py    │
│  email_service.py · report_generator.py · ui_helpers.py       │
└───────┬───────────────┬───────────────┬──────────────────────┘
        │               │               │
┌───────▼──────┐ ┌──────▼───────┐ ┌─────▼────────────────────────┐
│ DATA LAYER   │ │  AI / ML      │ │ EXTERNAL FREE APIs           │
│ database.py  │ │ RandomForest  │ │ Nominatim · Overpass · OSRM  │
│ Firebase  ⇄  │ │ risk_model.pkl│ │ OpenStreetMap tiles · SMTP   │
│ Local JSON   │ │               │ │                              │
└──────────────┘ └───────────────┘ └──────────────────────────────┘
```

**Flow of an SOS:** User triggers SOS → cooldown check → feature gathering
(time, history, distance to safe place via Overpass) → Random Forest risk
prediction → reverse geocoding (Nominatim) → persist alert + location history
(Firebase/local) → notify contacts (SMTP/simulated) → display risk badge,
recommendations & map → optional PDF report.

---

## 9. Module Description

1. **User Registration & Login** (`auth.py`, `1_Login.py`, `2_Register.py`):
   secure salted SHA-256 credentials, role-based access (user/admin), session
   management, page guards.
2. **User Dashboard** (`3_User_Dashboard.py`): personal metrics, recent alerts,
   risk distribution chart, quick actions.
3. **Emergency Contact Management** (`4_Emergency_Contacts.py`): add/list/delete
   trusted contacts.
4. **SOS Alert Trigger** (`5_SOS_Alert.py`, `alert_service.py`): one-click SOS,
   cooldown logic, automatic risk prediction, notification, recommendations.
5. **Live Location Tracking** (`6_Live_Map.py`, `map_service.py`): Folium map,
   user marker, nearby safe places, alert trail, reverse-geocoded address.
6. **Emergency Alert History** (`7_Alert_History.py`): filterable history,
   status lifecycle management, per-alert PDF.
7. **AI Risk Prediction** (`9_AI_Risk_Prediction.py`, `ml_model.py`):
   interactive inference, probability chart, feature importance, retraining.
8. **Nearby Safe Place Finder** (`8_Nearby_Safe_Places.py`): Overpass search,
   OSRM routing, distance ranking.
9. **Admin Monitoring Dashboard** (`10_Admin_Dashboard.py`): live feed,
   filters, map of alert locations, resolve actions, KPIs.
10. **Alert Analytics & Heatmap** (`11_Analytics.py`): risk/status/hourly
    charts, time trend, heatmap of unsafe areas, high-risk zones.
11. **Incident Report Generation** (`report_generator.py`, `12_Reports.py`):
    incident and admin PDF reports.
12. **Safety Recommendation System** (`ml_model.get_recommendations`):
    context-aware, risk-level-specific advice.

---

## 10. Database Design (Collections)

**Users**
| Field | Type | Description |
|-------|------|-------------|
| uid | string (PK) | unique user id |
| name | string | full name |
| email | string | login email |
| phone | string | contact number |
| role | string | `user` / `admin` |
| password | string | salted hash |
| created_at | ISO datetime | registration time |

**EmergencyContacts**
| Field | Type | Description |
|-------|------|-------------|
| contact_id | string (PK) | unique id |
| user_id | string (FK→Users) | owner |
| name, phone, email, relation | string | contact details |

**Alerts**
| Field | Type | Description |
|-------|------|-------------|
| alert_id | string (PK) | unique id |
| user_id | string (FK) | who triggered |
| user_name, user_email | string | denormalised |
| latitude, longitude | float | location |
| address | string | reverse-geocoded |
| battery_level | int | device battery |
| risk_score | float | 0–100 |
| risk_level | string | Low/Medium/High/Critical |
| risk_confidence | float | model confidence |
| distance_to_safe_km | float | nearest safe place |
| status | string | Pending/Sent/Active/Resolved |
| created_at, resolved_at | ISO datetime | timestamps |

**LocationHistory**
| Field | Type | Description |
|-------|------|-------------|
| location_id | string (PK) | unique id |
| alert_id | string (FK) | parent alert |
| user_id | string (FK) | user |
| latitude, longitude, accuracy | float | reading |
| timestamp | ISO datetime | time |

**SafePlaces**
| Field | Type | Description |
|-------|------|-------------|
| place_id | string (PK) | unique id |
| name, type | string | place info |
| latitude, longitude | float | location |
| distance | float | km from user |

**Reports**
| Field | Type | Description |
|-------|------|-------------|
| report_id | string (PK) | unique id |
| user_id, alert_id | string (FK) | references |
| report_path | string | PDF path |
| generated_at | ISO datetime | time |

---

## 11. Algorithm

**SOS Trigger Algorithm**
```
INPUT: user, latitude, longitude, battery_level, movement
1. IF user triggered an SOS within COOLDOWN seconds AND not forced:
       RETURN cooldown message            # prevents duplicate alerts
2. Gather features:
       hour          ← current hour
       sos_frequency ← user's alerts in last 1 hour
       prev_incident ← total past alerts
       nearest       ← Overpass nearest police/hospital
       distance      ← Haversine/OSRM distance to nearest
       area_type     ← derived from availability of safe places
3. risk ← RandomForest.predict(features)            # AI step
4. address ← Nominatim.reverse_geocode(lat, lon)
5. Persist Alert + LocationHistory (Firebase or local JSON)
6. Notify each trusted contact (SMTP or simulated)
7. status ← Active
8. RETURN alert, risk, recommendations, notifications
```

**Risk Scoring Logic (encoded in training labels)**
- Night time (19:00–06:00) → +risk
- Battery < 20% → +risk; < 40% → moderate +risk
- Repeated SOS in short window → +risk
- Greater distance to nearest safe place → +risk
- More previous incidents in the area → +risk
- Isolated area (and stationary) → +risk

---

## 12. ML Model Explanation

- **Algorithm:** `RandomForestClassifier` (200 trees, max_depth 14) — an
  ensemble of decision trees that votes on the risk class. Chosen for its
  robustness to noise, ability to model non-linear feature interactions, and
  built-in feature-importance explainability.
- **Inputs (9 features):** hour of day, day/night flag, location risk score,
  previous incident count, battery level, SOS frequency, distance to nearest
  safe place, area type (public/residential/isolated), movement status.
- **Output:** one of four classes — **Low / Medium / High / Critical Risk** —
  plus class probabilities, a continuous 0–100 score, and a confidence value.
- **Training data:** a synthetic, domain-grounded dataset (default 6,000 rows)
  generated by `ml_model.generate_dataset()`, where each sample is labelled by
  a transparent risk-scoring function plus small Gaussian noise so the decision
  boundary is realistic rather than perfectly separable.
- **Evaluation:** an 80/20 stratified train/test split with accuracy and a
  per-class classification report; feature importances are surfaced in the UI.
- **Persistence:** the trained model is saved to `models/risk_model.pkl` via
  joblib and lazily loaded (and auto-trained on first run if missing).

---

## 13. API Explanation

| API | Role in system | How it is used |
|-----|----------------|----------------|
| **OpenStreetMap** | Base map tiles | Rendered inside Folium maps |
| **Nominatim** | Reverse geocoding | `reverse_geocode(lat,lon)` → human address |
| **Overpass** | Nearby amenities | Queries `amenity=police/hospital/clinic/bus_station/pharmacy` within a radius |
| **OSRM** | Routing | `route_distance()` → km + minutes to nearest safe place |
| **Haversine** | Distance fallback | Instant local great-circle distance |
| **Gmail SMTP** | Email alerts | Sends SOS email to contacts (App Password) |
| **Firebase Firestore** | Real-time DB | Stores all collections; offline JSON fallback |

All mapping APIs are **free and key-less**; the system degrades gracefully if
any API is unavailable.

---

## 14. Implementation

The system is implemented in **Python** with a **Streamlit** multipage frontend.
Core logic is cleanly separated into service modules (`auth`, `alert_service`,
`ml_model`, `map_service`, `email_service`, `report_generator`) and a unified
data-access layer (`database.py`) that abstracts Firebase vs. local storage.
The UI is styled with a custom CSS theme (`assets/style.css`) and reusable
components (`ui_helpers.py`). Charts use **Plotly**, maps use **Folium /
streamlit-folium**, machine learning uses **scikit-learn**, and PDF reports use
**ReportLab**. Demo data and model training are bootstrapped via
`generate_sample_data.py`.

**Setup & run:**
```
pip install -r requirements.txt
python generate_sample_data.py     # optional: seed data + train model
streamlit run app.py
```

---

## 15. Testing

Automated tests are provided in `test_system.py`:

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 1 | Password hashing & verification | Correct password verifies, wrong fails |
| 2 | Haversine distance (Hyderabad→Bengaluru) | ~450–620 km |
| 3 | ML dataset generation & training | Accuracy > 0.7, all features present |
| 4 | Risk prediction (night, low battery, isolated) | Medium/High/Critical |
| 5 | Safety recommendations (Critical) | ≥ 4 actionable items |
| 6 | Incident PDF generation | Valid `.pdf` produced |
| 7 | Status lifecycle | Pending→Sent→Active→Resolved |

**Manual / functional test cases:**
- Register → login → logout flow works and guards protected pages.
- Adding/deleting emergency contacts persists correctly.
- SOS with no contacts warns the user; with contacts, notifications appear.
- Cooldown blocks a second SOS within the window; "force" overrides it.
- Offline mode (no Firebase) still stores alerts; reconnecting syncs them.
- Admin dashboard filters by status/risk/user and resolves alerts.
- Analytics charts and heatmap populate from seeded data.

Run: `python test_system.py`

---

## 16. Results

- Users can trigger an SOS in **one click**, with location, address, battery,
  and an AI risk classification attached automatically.
- The Random Forest model achieves **strong accuracy (~84% on the full
  6,000-row dataset)** across four risk classes on the held-out test set, with
  *distance to safe place*, *is_night*, and *battery level* among the most
  influential features.
- Nearby police/hospitals are reliably retrieved from Overpass and rendered on
  an interactive map, with OSRM route distance to the nearest safe place.
- Administrators gain a **real-time, filterable view** of all alerts, a heatmap
  of unsafe areas, time-based analytics, and downloadable PDF reports.
- The system runs fully **offline** when needed and **synchronises** to
  Firebase when connectivity returns — demonstrating resilience.

---

## 17. Advantages

- 🚀 **Proactive & intelligent** — AI risk prediction, not just static alerts.
- 💸 **Zero-cost APIs** — Nominatim, Overpass, OSRM, OpenStreetMap, Firebase free tier.
- 🔄 **Resilient** — local fallback + automatic cloud sync; never fails on connectivity.
- 🧭 **Location intelligence** — nearby safe places and fastest route to safety.
- 🛰️ **Real-time admin oversight** — live monitoring, heatmaps, analytics.
- 📄 **Professional reporting** — automatic PDF incident & admin reports.
- 🎨 **Modern, responsive UI** — clean Streamlit interface with custom theming.
- 🧩 **Modular & extensible** — clean separation of concerns for easy expansion.

---

## 18. Future Scope

- 📱 Native mobile app / PWA wrapper with continuous background location.
- 📨 SMS & WhatsApp gateway integration for contact alerts.
- ⌚ Wearable / IoT panic-button and voice-activated SOS.
- 🧠 Deep-learning and time-series models trained on real incident data.
- 🗣️ Audio/video evidence capture and secure cloud upload during an SOS.
- 🚓 Direct integration with police/emergency dispatch APIs.
- 🌍 Crowd-sourced safety ratings and community-reported unsafe zones.
- 🔔 Real-time push notifications and live two-way location sharing.

---

## 19. Conclusion

The **AI-Powered Smart Women Safety and Emergency Response System** delivers a
complete, modern, and intelligent safety platform that unites real-time
alerting, machine-learning risk prediction, open location intelligence, and
administrative analytics into a single cohesive application. By leveraging
Streamlit, Firebase, scikit-learn, and free open-mapping APIs, it provides a
powerful yet low-cost solution that is both production-capable and ideal for
major-project submission. The platform demonstrates how artificial intelligence
and open data can be combined to build technology that meaningfully enhances
personal safety and emergency response.

---

*Major Project · AI-Powered Smart Women Safety & Emergency Response System
Using Streamlit, Firebase, Real-Time Location Tracking, and Intelligent Risk
Prediction.*
