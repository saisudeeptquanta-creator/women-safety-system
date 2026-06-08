# 🛡️ AI-Powered Smart Women Safety and Emergency Response System

**Using Streamlit, Firebase, Real-Time Location Tracking, and Intelligent Risk Prediction**

A complete, professional, AI-powered emergency safety platform. Users can send
one-click SOS alerts to trusted contacts with their live location, an
AI-computed risk score, and safety recommendations. Administrators get a
real-time monitoring dashboard with analytics, heatmaps of unsafe areas, and
PDF reporting.

---

## ✨ Key Features

### User
- 🔐 Registration & login (secure salted hashing)
- 👥 Trusted emergency contact management
- 🚨 One-click SOS with cooldown (no duplicate spam)
- 📍 Live location capture (browser GPS or manual)
- 🤖 Automatic AI risk prediction during every SOS
- 🗺️ Live map with nearby safe places & alert trail
- 🏥 Nearby police / hospitals / clinics / bus stations / pharmacies
- 🧭 Route & distance to the nearest safe place (OSRM)
- 📜 Alert history with status lifecycle (Pending → Sent → Active → Resolved)
- 📄 Professional PDF incident reports

### Admin
- 🛰️ Real-time alert monitoring feed
- 🔎 Filter by status, risk level, user
- 🗺️ Alert locations on a live map
- 🔥 Heatmap of unsafe areas + high-risk zone table
- 📈 Time-based & risk analytics
- 📊 System-wide PDF admin report

### AI / ML
- 🌲 **Random Forest Classifier** predicting **Low / Medium / High / Critical** risk
- Features: hour, day/night, location risk, previous incidents, battery,
  SOS frequency, distance to safe place, area type, movement status
- Synthetic, domain-grounded training dataset generator
- Feature-importance explainability in the UI

---

## 🧰 Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend/UI | Streamlit (multipage) + custom CSS |
| Backend logic | Python |
| Database | Firebase Firestore (**+ local JSON fallback**) |
| Auth | Custom secure Streamlit auth (Firebase-ready) |
| Maps | Folium + streamlit-folium + OpenStreetMap tiles |
| Charts | Plotly |
| ML | scikit-learn Random Forest |
| Reports | ReportLab (PDF) |
| Free APIs | Nominatim, Overpass, OSRM, OpenStreetMap |
| Email | Gmail SMTP (free) with simulated fallback |

---

## 📁 Project Structure

```
women_safety_system/
├── app.py                      # Home / entry point
├── requirements.txt
├── README.md
├── DOCUMENTATION.md            # Full project documentation
├── firebase_config.py          # Firebase init (fail-safe)
├── database.py                 # Unified DB layer + offline sync
├── auth.py                     # Authentication & sessions
├── ml_model.py                 # Dataset gen + RF training + inference
├── alert_service.py            # SOS orchestration + cooldown
├── map_service.py              # Nominatim / Overpass / OSRM / Folium
├── report_generator.py         # PDF reports (ReportLab)
├── email_service.py            # SMTP / simulated notifications
├── ui_helpers.py               # Shared UI components & theme
├── generate_sample_data.py     # Seed demo data + train model
├── test_system.py              # Test cases
├── pages/
│   ├── 1_Login.py
│   ├── 2_Register.py
│   ├── 3_User_Dashboard.py
│   ├── 4_Emergency_Contacts.py
│   ├── 5_SOS_Alert.py
│   ├── 6_Live_Map.py
│   ├── 7_Alert_History.py
│   ├── 8_Nearby_Safe_Places.py
│   ├── 9_AI_Risk_Prediction.py
│   ├── 10_Admin_Dashboard.py
│   ├── 11_Analytics.py
│   └── 12_Reports.py
├── models/risk_model.pkl       # (auto-generated on first run)
├── data/                       # datasets + local JSON store
├── assets/                     # style.css, siren.mp3, logo.png
└── reports/                    # generated PDFs
```

---

## 🚀 Quick Start

```powershell
# 1. (Recommended) create a virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional but recommended) seed demo data + train the model
python generate_sample_data.py

# 4. Launch the app
streamlit run app.py
```

Open the browser at `http://localhost:8501`.

**Demo admin login:** `admin@safety.com` / `admin123`
**Demo user login:**  `aisha@example.com` / `password123` (after seeding)

> The app runs **out-of-the-box without Firebase** — it automatically uses a
> local JSON store and trains the ML model on first launch.

---

## 🔥 Firebase Setup (optional — enables real-time cloud database)

1. Go to <https://console.firebase.google.com> and create a project (free tier).
2. **Build → Firestore Database → Create database** (start in test mode).
3. **Project settings → Service accounts → Generate new private key.**
   Download the JSON file.
4. Provide the credentials in **any one** of these ways:
   - Save the file as `serviceAccountKey.json` in the project root, **or**
   - Create `.streamlit/secrets.toml`:
     ```toml
     [firebase]
     type = "service_account"
     project_id = "your-project-id"
     private_key_id = "..."
     private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
     client_email = "...@...iam.gserviceaccount.com"
     client_id = "..."
     auth_uri = "https://accounts.google.com/o/oauth2/auth"
     token_uri = "https://oauth2.googleapis.com/token"
     auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
     client_x509_cert_url = "..."
     ```
   - Or set environment variable `FIREBASE_CREDENTIALS` to the raw JSON string.
5. Restart the app. The sidebar will show **"Firebase (online)"** and any
   alerts buffered offline are automatically synced.

---

## 🌐 Free API Setup (no keys required!)

| API | Purpose | Endpoint |
|-----|---------|----------|
| **Nominatim** | Reverse geocode lat/lon → address | `nominatim.openstreetmap.org` |
| **Overpass** | Nearby police, hospitals, clinics, bus stations, pharmacies | `overpass-api.de` |
| **OSRM** | Route distance & duration to safe place | `router.project-osrm.org` |
| **OpenStreetMap** | Map tiles in Folium | tile server |

All four are **free and key-less**. Please respect fair-use rate limits.
If any API is unreachable the app degrades gracefully (e.g. Haversine
distance instead of OSRM).

### Email alerts (optional)
Add to `.streamlit/secrets.toml`:
```toml
[email]
sender = "yourgmail@gmail.com"
app_password = "your-16-char-gmail-app-password"
```
Without this, contact notifications are **simulated** and still shown in the UI.

---

## 🧪 Testing

```powershell
python test_system.py
```
Covers password hashing, Haversine math, ML dataset/training, risk prediction,
recommendations, PDF generation and the status lifecycle.

---

## 🤖 Regenerate dataset & retrain the model

```powershell
python ml_model.py
```
This regenerates `data/risk_training_data.csv` and `models/risk_model.pkl`,
and prints accuracy + top feature importances.

---

## ☁️ Deploy to Streamlit Community Cloud (free)

1. **Push this folder to a GitHub repo** (see commands below).
2. Go to <https://share.streamlit.io> → **Sign in with GitHub** → **Create app**.
3. Select your repository and branch, and set:
   - **Main file path:** `app.py`  (this folder is the repo root)
   - **Advanced settings → Python version:** `3.12` or `3.13` (recommended).
4. **Add secrets** (App → ⚙️ Settings → **Secrets**): paste the Firebase
   and/or `[email]` blocks from `.streamlit/secrets.toml.example`.
   *(Optional — the app runs without them in local-JSON mode.)*
5. Click **Deploy**. First boot trains the ML model automatically (a few
   seconds). Log in as **admin@safety.com / admin123**, open the **Admin
   Dashboard**, and click **"Load demo data"** to populate analytics.

**Push to GitHub:**
```powershell
cd women_safety_system
git init
git add .
git commit -m "Initial commit: AI Women Safety System"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

> ⚠️ **Persistence note:** Streamlit Cloud storage is *ephemeral* — the local
> JSON store and trained model reset when the app restarts. For permanent
> real-time data, configure **Firebase** in Secrets (step 4); the app then
> stores everything in Firestore and survives restarts.

---

## 📚 Documentation

Full project documentation (Abstract, Problem Statement, Architecture, Module
Description, Database Design, Algorithm, Testing, Results, Future Scope, etc.)
is in **[DOCUMENTATION.md](DOCUMENTATION.md)** — ready for major-project
submission.

---

*Major Project · AI-Powered Smart Women Safety & Emergency Response System*
