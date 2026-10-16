# 🌿 EcoCampus AI — Sustainable Campus Intelligence Platform

> **"EcoCampus AI transforms campus sustainability data into understandable insights and prioritized actions, helping institutions move from monitoring problems to measuring improvements."**

EcoCampus AI is a sustainability operations prototype combining **YOLOv8 image review**, **SQLite work orders**, an **illustrative DSU facility schematic**, **historical user-uploaded meter data**, and a clearly labeled **demo telemetry simulator**. No physical DSU sensor or camera network is connected.

---

## 📑 Table of Contents

1. [Architecture & System Flow](#-architecture--system-flow)
2. [What Was Broken & How It Was Fixed](#-what-was-broken--how-it-was-fixed-the-json-error)
3. [Project Folder Structure](#-project-folder-structure)
4. [Quickstart Guide for Windows](#-quickstart-guide-for-windows)
5. [How to Run the Application](#-how-to-run-the-application)
6. [API Reference & Testing Guide](#-api-reference--testing-guide)
7. [Manual Testing Checklist](#-manual-testing-checklist)
8. [Hackathon Demonstration Script (Step-by-Step)](#-hackathon-demonstration-script)
9. [Feature Matrix & Future Enhancements](#-feature-matrix--future-enhancements)

---

## 🏛 Architecture & System Flow

```
[ Campus Camera / User Upload ]
            │ (JPG / PNG <= 8MB)
            ▼
┌──────────────────────────────────────┐
│       Frontend (Vanilla JS + CSS)     │
│  - Client-side validation            │
│  - Instant preview & sample picker   │
│  - Dynamic API Base URL routing      │
│  - Safe JSON response parser         │
└──────────────────┬───────────────────┘
                   │ POST multipart/form-data
                   ▼
┌────────────────────────────────────────────────────────┐
│               Python Flask API Server (Port 5000)      │
│  - Ultralytics YOLOv8n object detection                │
│  - COCO waste ontology mapping (Recyclable/Organic)    │
│  - Bounding box rendering -> static/latest_detection.jpg│
│  - SQLite persistence -> campus.db                     │
│  - Historical CSV meter imports & 1.25x anomaly flags  │
│  - Explicitly simulated telemetry scenarios             │
└──────────────────┬─────────────────────────────────────┘
                   │ Structured JSON response
                   ▼
┌────────────────────────────────────────────────────────┐
│            Interactive Operations Dashboard            │
│  - Annotated image display with bounding boxes         │
│  - Human-in-the-Loop confirmation modal                │
│  - DSU facility schematic (not to scale)                │
│  - Work orders with crew assignment and SLA             │
│  - Optional facility-linked alerts and YOLO evidence    │
│  - Estimate-based cost and Scope 2 calculator           │
│  - Executive Printable Report & CSV Export             │
└────────────────────────────────────────────────────────┘
```

### DSU Campus Reference & Data Limits

The interactive schematic uses broad facilities named or described in the official [DSU E-brochure (2024)](https://dsu.edu.in/images/E_brochure_08022024.pdf): academic/research facilities and libraries (pp. 8-9, 16), innovation labs and maker spaces (pp. 8-9), integrated solar features (pp. 2-3), sports facilities (pp. 20-21), and CDSIMER with its teaching hospital (pp. 20-21). The brochure does not provide georeferenced building outlines or marker coordinates, so marker placement and connectors are illustrative and explicitly not to scale.

No DSU energy, water, waste, or camera network is configured. The telemetry HUD is a server-side **demo simulator**, not a live sensor feed. CSV imports are stored as historical, user-provided readings and are only associated with a map facility when the uploaded row identifies a recognized `facility_id` or exact brochure facility name. Existing alerts without an explicit facility association remain in the action center and are not placed on the schematic. A YOLO-confirmed waste observation becomes a work order only after human confirmation; the selected facility link is optional.

Financial and environmental totals are estimates from energy, water, and waste quantities entered on completed work orders. Tariffs are $0.14/kWh and ₹8.5/kWh, $0.004/L and ₹0.25/L; Scope 2 uses 0.82 kg CO₂e/kWh. The calculator does not verify utility bills, fuel use, or actual emissions. Empty work-order estimates produce zero savings.

The webcam scanner requests browser permission and runs YOLO on a captured still frame; it is not a campus CCTV feed. Camera-originated confirmed work orders are labeled `Webcam AI Verified Detection`.

---

## 🔍 What Was Broken & How It Was Fixed (The JSON Error)

### The Problem:
The frontend was displaying:
```
"Failed to execute 'json' on 'Response': Unexpected end of JSON input"
```

### Root Cause Analysis:
1. **Origin & Port Mismatch with VS Code Live Server**: 
   When running the frontend via VS Code Live Server (`http://127.0.0.1:5500`), a relative fetch to `/api/detect-waste` went to port **5500**, not Flask's port **5000**. Live Server returned an empty response or an HTML 404 page.
2. **Unsafe `response.json()` Execution**:
   The frontend called `await response.json()` before inspecting `response.ok` or checking content type. When trying to parse an empty body or HTML `<doctype>`, JavaScript crashed with `Unexpected end of JSON input`.
3. **Missing Static Route for Annotated Detections**:
   The backend saved detection images to `static/latest_detection.jpg` without an explicit static route or CORS-safe serving path for cross-origin frontend servers.

### The Fix:
- **Dynamic API Base Routing**: In `script.js`, the app detects the current origin:
  ```javascript
  const API_BASE = (window.location.port === "5000") ? "" : "http://127.0.0.1:5000";
  ```
- **Safe Fetch Wrapper (`safeFetchJson`)**:
  Reads `response.text()` first. If non-JSON or HTML is returned, it provides a friendly diagnostic message: *"Received HTML/empty response. Ensure Flask is running on port 5000."*
- **Explicit Static Serving & CORS**:
  Flask response headers enable cross-origin requests from Live Server (port 5500), while the static route serves annotated images from the Flask API.
- **Consistent JSON Error Payloads**:
  All Flask endpoints return `{"success": true/false, "message": "..."}` with correct HTTP status codes (200, 400, 413, 500).

---

## 📁 Project Folder Structure

```
EcoCampus-AI/
├── index.html              # Modern single-page operations center dashboard
├── style.css               # Dark navy & emerald green responsive styling
├── script.js               # Frontend application logic, safe API client & UI sync
├── requirements.txt        # Python backend dependencies
├── .gitignore              # Local environment and generated output exclusions
├── yolov8n.pt              # Pretrained YOLOv8 weights (auto-detected)
├── README.md               # Complete setup, testing, and demonstration manual
├── sample_images/          # Preloaded demo images for 1-click hackathon testing
│   ├── sample_campus_bus.jpg
│   ├── canteen_bottles.jpg
│   └── cafeteria_tray.jpg
└── backend/
    ├── app.py              # Flask server, YOLO inference, SQLite DB & routes
    ├── campus.db           # SQLite database for persistent maintenance alerts
    └── static/
        ├── latest_detection.jpg   # Annotated inference image
        └── detections/            # Timestamped detection archives
```

---

## 💻 Quickstart Guide for Windows

### Prerequisites:
- Windows 10 or 11
- Python 3.10, 3.11, or 3.12 installed
- VS Code (optional: Live Server extension)

### Step 1: Open PowerShell
Press `Win + X` and select **Terminal** or **PowerShell**, then navigate to the project:
```powershell
cd C:\Users\DELL\OneDrive\Desktop\EcoCampus-AI
```

### Step 2: Create the Project Environment and Install Dependencies
From the project root, create and activate a virtual environment, then install the backend packages:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
*(If PowerShell says script execution is restricted, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

---

## 🚀 How to Run the Application

### Option A: Run Everything Through Flask (Recommended - Single Command!)
```powershell
python backend\app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

Both the frontend and the AI backend will run together on port 5000!

---

### Option B: Run with VS Code Live Server
1. In VS Code, right-click `index.html` and choose **"Open with Live Server"** (runs at `http://127.0.0.1:5500`).
2. In a separate terminal window, start the Flask backend:
   ```powershell
   python backend\app.py
   ```
3. Look at the topbar in your browser:
   - When Flask is running, it will automatically show: `● AI ENGINE CONNECTED (PORT 5000)`.

---

## 📡 API Reference & Testing Guide

You can test every endpoint using PowerShell or `curl`:

### 1. Health Check
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health" -Method Get
```
**Expected Output:**
```json
{
  "database": "SQLite (campus.db)",
  "model": "YOLOv8n Pretrained Object Detector",
  "model_loaded": true,
  "service": "EcoCampus AI Platform",
  "status": "online",
  "success": true
}
```

### 2. Fetch Campus Telemetry & Digital Twin Data
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/campus-data" -Method Get
```

### 3. Fetch Maintenance Alerts (Persistent in SQLite)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/alerts" -Method Get
```

### 4. Create a Maintenance Alert
```powershell
$body = @{
    title = "Water tap dripping in Block A Washroom"
    category = "Water"
    location = "Block A"
    priority = "Medium"
    evidence = "Manual observation during rounds"
    action = "Replace washer valve"
    status = "Open"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/alerts" -Method Post -Body $body -ContentType "application/json"
```

### 5. Update Alert Status (Open -> In Progress -> Completed)
```powershell
$update = @{ status = "Completed" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/alerts/1" -Method Patch -Body $update -ContentType "application/json"
```

---

## Manual Verification Checklist

| # | Test Scenario | Expected Result |
|---|---------------|-----------------|
| 1 | **Backend Health Check** | `/api/health` returns online status, model availability, and `physical_sensor_feed: false`. |
| 2 | **Demo Telemetry** | HUD reads `DEMO SIMULATOR`; offline state clears readings rather than generating client-side values. |
| 3 | **Simulation Controls** | Each scenario adds a `Demo Simulation` work order; Reset completes only those scenario orders. |
| 4 | **Camera Capture** | Browser permission is requested; captured still frames run YOLO locally through the existing API. |
| 5 | **CSV Import** | Energy, water, and waste units are parsed separately, persisted, and flagged above 1.25x grouped means. |
| 6 | **Facility Data** | Imported facility readings show filename/timestamp; no readings appear until an associated import exists. |
| 7 | **Work Orders** | Search, facility link, crew assignment, SLA deadline, status, resolution notes, and delete persist in SQLite. |
| 8 | **ESG Calculator** | Currency toggle updates tariffs; only entered estimates on completed work orders contribute to totals. |
| 9 | **Data Export** | CSV export includes all work orders and persisted meter readings with source/anomaly fields. |
| 10 | **DSU Map** | All, Energy, Water, Waste, and Alerts filters update visible markers; schematic positions remain labeled illustrative. |

---

## 🎤 Hackathon Demonstration Script

Use this 3-minute presentation script during your team's demonstration:

### Minute 1: The Problem & The Solution
> *"Judges, college campuses generate hundreds of tons of waste and consume millions of gallons of water annually. Most campus facilities manage waste, energy, and water through disconnected spreadsheets or delayed student complaints. 
> 
> Meet **EcoCampus AI** — an AI-powered operations center that connects visual observations with automated sensor intelligence and prioritized maintenance workflows."*

### Minute 2: Live AI Waste Detection & Human Verification
> *(Point to the screen at `#waste-intelligence`)*
> 
> *"Here is our main AI engine. A student volunteer or custodial staff member snaps a photo of a campus dining area. With one click, our pretrained YOLOv8 model inspects the image.*
> 
> *(Click '🥤 Canteen Bottles' -> click 'Analyze Image with AI')*
> 
> *In under 400 milliseconds, YOLO identifies recyclable plastic bottles with confidence scores and draws bounding boxes. 
> 
> But notice our ethical AI design: COCO detects objects, not intent. So we provide a **Human-in-the-Loop Verification** step. The facility manager clicks 'Confirm as Waste Alert', which pre-fills our maintenance ticket with exact AI evidence and dispatches the custodial team to the Canteen."*

### Minute 3: Digital Twin & Measuring Real Improvements
> *(Scroll to `#campus-twin` and click on Library, then Block C)*
> 
> *"Next is our **Campus Digital Twin**. Every building shows live-style telemetry. For example, our transparent rule-based anomaly detector noticed that the Library had a continuous 165 L/hr water draw at 3:00 AM while closed — pinpointing a concealed plumbing leak before flooding occurs.*
> 
> *(Scroll to `#action-center` and toggle an alert to 'Completed')*
> 
> *Finally, in our Priority Action Center backed by SQLite, once maintenance resolves an issue, our Campus Sustainability Score immediately climbs, and our verified environmental impact metrics update in real time. We can now export a full executive audit for university administration."*

---

## 🔮 Feature Matrix & Future Enhancements

### Implemented in Hackathon MVP:
- [x] Full-stack architecture with Flask, YOLOv8, and SQLite
- [x] Pretrained computer vision detection with annotated visual bounding boxes
- [x] Ethical Human-in-the-Loop verification workflow
- [x] Dynamic API base auto-routing (fixes VS Code Live Server port conflicts)
- [x] DSU brochure-referenced illustrative campus schematic (not geographic)
- [x] Clearly labeled demo telemetry scenarios; no physical feeds configured
- [x] Persistent work-order CRUD, crew assignment, SLAs, and resolution notes
- [x] Historical CSV meter imports with 1.25x mean anomaly flags
- [x] Estimate-based utility cost and Scope 2 calculator from completed work orders
- [x] 1-Click test image loader for seamless hackathon demonstrations
- [x] Printable executive reports and CSV dataset export

### Roadmap for Post-Hackathon & Campus Deployment:
- [ ] Train a dedicated waste-classification YOLO model on Taco / TrashNet datasets
- [ ] Connect real MQTT / Modbus smart IoT energy meters and pulse water flow sensors
- [ ] Role-based authentication (Admin, Custodial Staff, Student Volunteer)
- [ ] Automated SMS / Push notifications for urgent level-1 leak alerts
