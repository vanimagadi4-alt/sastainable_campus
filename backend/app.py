"""EcoCampus AI Flask API for YOLO review, work orders, and meter imports."""

import csv
import io
import math
import os
import random
import re
import secrets
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO
from werkzeug.security import check_password_hash, generate_password_hash

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
STATIC_DIR = BACKEND_DIR / "static"
DETECTIONS_DIR = STATIC_DIR / "detections"
SAMPLE_IMAGES_DIR = PROJECT_ROOT / "sample_images"
for directory in (STATIC_DIR, DETECTIONS_DIR, SAMPLE_IMAGES_DIR):
    directory.mkdir(parents=True, exist_ok=True)

DB_PATH = BACKEND_DIR / "campus.db"
BROCHURE_URL = "https://dsu.edu.in/images/E_brochure_08022024.pdf"
CREWS = {"Facility Crew Alpha", "Plumbing Unit 2", "Green Volunteers Guild"}

DSU_FACILITIES = {
    "academic-research": {
        "name": "Academic & research facilities",
        "description": "Laboratories, research centers, and interdisciplinary academic spaces.",
        "source_pages": "8-9, 16"
    },
    "library": {
        "name": "Library & scholarly resources",
        "description": "Libraries and digital scholarly resources described in the campus brochure.",
        "source_pages": "16"
    },
    "innovation-maker": {
        "name": "Innovation labs & maker spaces",
        "description": "Innovation labs, maker spaces, and collaborative learning zones.",
        "source_pages": "8-9"
    },
    "sports-fitness": {
        "name": "Sports & fitness facilities",
        "description": "Sports and fitness facilities described in the campus brochure.",
        "source_pages": "20-21"
    },
    "medical-campus": {
        "name": "CDSIMER medical college & teaching hospital",
        "description": "The brochure identifies CDSIMER and its teaching hospital on campus.",
        "source_pages": "20-21"
    },
    "solar-infrastructure": {
        "name": "Integrated solar features",
        "description": "Integrated solar panels are described; exact locations are not provided.",
        "source_pages": "2-3"
    }
}

WASTE_CATEGORIES = {
    "recyclable": {
        "bottle": "Plastic / Glass Bottle", "cup": "Disposable / Paper Cup",
        "wine glass": "Glass Container", "can": "Aluminum Can", "tin": "Metal Tin",
        "fork": "Plastic Cutlery", "knife": "Plastic Cutlery", "spoon": "Plastic Cutlery"
    },
    "organic": {
        "banana": "Organic Fruit Peel", "apple": "Organic Fruit Core",
        "sandwich": "Food Waste / Scrap", "orange": "Organic Fruit Peel",
        "broccoli": "Organic Vegetable Waste", "carrot": "Organic Vegetable Waste",
        "pizza": "Food Scrap / Crust", "donut": "Food Waste", "cake": "Food Waste"
    },
    "packaging": {
        "bowl": "Takeout Food Bowl", "box": "Cardboard / Shipping Box",
        "bag": "Plastic / Paper Bag", "backpack": "Personal Item (Not Waste)",
        "handbag": "Personal Item (Not Waste)"
    }
}
ALL_WASTE_LABELS = set().union(*(set(category) for category in WASTE_CATEGORIES.values()))

app = Flask(__name__, static_folder=str(STATIC_DIR))
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["SECRET_KEY"] = os.environ.get("ECONOVA_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
    return response


model_path = PROJECT_ROOT / "yolov8n.pt"
if not model_path.exists():
    model_path = BACKEND_DIR / "yolov8n.pt"
if not model_path.exists():
    model_path = "yolov8n.pt"
model = YOLO(str(model_path))


def get_db():
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()
    connection.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            priority TEXT NOT NULL,
            evidence TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'Manual Inspection',
            impact_estimate TEXT,
            facility_id TEXT,
            assignee TEXT DEFAULT 'Facility Crew Alpha',
            notes TEXT DEFAULT '',
            sla_hours INTEGER DEFAULT 4,
            cost_savings REAL DEFAULT 0.0,
            co2_savings REAL DEFAULT 0.0,
            energy_savings_kwh REAL DEFAULT 0.0,
            water_savings_liters REAL DEFAULT 0.0,
            waste_diverted_kg REAL DEFAULT 0.0
        )
    """)
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(alerts)")}
    migrations = {
        "facility_id": "TEXT", "assignee": "TEXT DEFAULT 'Facility Crew Alpha'",
        "notes": "TEXT DEFAULT ''", "sla_hours": "INTEGER DEFAULT 4",
        "cost_savings": "REAL DEFAULT 0.0", "co2_savings": "REAL DEFAULT 0.0",
        "energy_savings_kwh": "REAL DEFAULT 0.0", "water_savings_liters": "REAL DEFAULT 0.0",
        "waste_diverted_kg": "REAL DEFAULT 0.0"
    }
    for column, sql_type in migrations.items():
        if column not in columns:
            connection.execute(f"ALTER TABLE alerts ADD COLUMN {column} {sql_type}")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS meter_imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            imported_at TEXT NOT NULL,
            reading_count INTEGER NOT NULL
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS meter_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_id INTEGER NOT NULL REFERENCES meter_imports(id) ON DELETE CASCADE,
            facility_id TEXT,
            facility_label TEXT,
            metric TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            measured_at TEXT NOT NULL,
            is_anomaly INTEGER NOT NULL DEFAULT 0
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('admin', 'student')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_login_at TEXT
        )
    """)
    connection.commit()
    connection.close()


def add_sla_details(alert):
    try:
        created = datetime.strptime(alert["created_at"], "%Y-%m-%d %H:%M")
        due = created + timedelta(hours=int(alert.get("sla_hours") or 4))
    except (TypeError, ValueError):
        alert["due_at"] = None
        alert["sla_breached"] = False
        return alert
    alert["due_at"] = due.strftime("%Y-%m-%d %H:%M")
    alert["sla_breached"] = alert["status"] != "Completed" and datetime.now() > due
    return alert


init_db()


@app.before_request
def require_dashboard_login():
    # Keep health and sign-in endpoints public. Dashboard APIs require a session.
    if request.path.startswith("/api/") and request.path not in {
        "/api/health", "/api/signup", "/api/login", "/api/logout", "/api/me"
    } and not session.get("user_id"):
        return jsonify({"error": "Please log in to continue."}), 401

TELEMETRY_STATE = {
    "simulation_mode": "normal",
    "base_energy_kw": 1284.0,
    "base_water_lps": 2.95,
    "base_solar_kw": 418.5,
    "base_occupancy": 3420,
    "history": [],
    "events": [{
        "time": datetime.now().strftime("%H:%M:%S"),
        "category": "system",
        "text": "Demo telemetry simulator ready. No physical meter feed is connected."
    }]
}

SIMULATION_SCENARIOS = {
    "energy_spike": {
        "category": "Energy", "priority": "High", "facility_id": "academic-research",
        "title": "Demo scenario: elevated facility power load", "assignee": "Facility Crew Alpha", "sla_hours": 4,
        "action": "Review the simulated load scenario; no physical asset was identified."
    },
    "water_leak": {
        "category": "Water", "priority": "High", "facility_id": "library",
        "title": "Demo scenario: abnormal water-flow pattern", "assignee": "Plumbing Unit 2", "sla_hours": 4,
        "action": "Review the simulated flow scenario; no physical meter or fixture was identified."
    },
    "waste_overflow": {
        "category": "Waste", "priority": "Medium", "facility_id": None,
        "title": "Demo scenario: waste overflow observation", "assignee": "Green Volunteers Guild", "sla_hours": 12,
        "action": "Review the simulated waste scenario; no DSU bin location is verified."
    }
}


@app.route("/")
def home():
    return redirect("/dashboard" if session.get("user_id") else "/login")


@app.route("/login")
def login_page():
    if session.get("user_id"):
        return redirect("/dashboard")
    return send_from_directory(PROJECT_ROOT / "EcoNova login page", "index2.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect("/login")
    return send_from_directory(PROJECT_ROOT, "index.html")


@app.post("/api/signup")
def signup():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters."}), 400
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]{2,}", email):
        return jsonify({"error": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    connection = get_db()
    try:
        cursor = connection.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, 'student')",
            (username, email, generate_password_hash(password))
        )
        connection.commit()
        return jsonify({"user": {"id": cursor.lastrowid, "username": username, "email": email, "role": "student"}}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "That username or email is already registered."}), 409
    finally:
        connection.close()


@app.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    requested_role = str(payload.get("role", "Student")).lower()
    connection = get_db()
    user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        connection.close()
        return jsonify({"error": "Incorrect email or password."}), 401
    if user["role"] != requested_role:
        connection.close()
        return jsonify({"error": f"This account is not registered as {requested_role.title()}."}), 403
    connection.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
    connection.commit()
    connection.close()
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["email"] = user["email"]
    session["role"] = user["role"]
    session.permanent = bool(payload.get("remember"))
    return jsonify({"user": {"id": user["id"], "username": user["username"], "email": user["email"], "role": user["role"]}})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/me")
def current_user():
    if not session.get("user_id"):
        return jsonify({"error": "Please log in."}), 401
    return jsonify({"user": {key: session.get(key) for key in ("user_id", "username", "email", "role")}})


@app.route("/style.css")
def stylesheet():
    return send_from_directory(PROJECT_ROOT, "style.css")


@app.route("/script.js")
def javascript():
    return send_from_directory(PROJECT_ROOT, "script.js")


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.route("/sample_images/<path:filename>")
def serve_sample_images(filename):
    return send_from_directory(SAMPLE_IMAGES_DIR, filename)


@app.route("/sample_meter_data.csv")
def sample_meter_template():
    return send_from_directory(PROJECT_ROOT, "sample_meter_data.csv", as_attachment=True)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True, "status": "online", "service": "EcoCampus AI",
        "model": "YOLOv8n Pretrained Object Detector", "model_loaded": True,
        "database": "SQLite (campus.db)", "telemetry_mode": "DEMO_SIMULATOR",
        "physical_sensor_feed": False, "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/api/telemetry/live-tick", methods=["GET"])
def live_tick():
    mode = TELEMETRY_STATE["simulation_mode"]
    energy = TELEMETRY_STATE["base_energy_kw"] * (1 + random.uniform(-0.015, 0.015))
    water = TELEMETRY_STATE["base_water_lps"] * (1 + random.uniform(-0.02, 0.02))
    solar = TELEMETRY_STATE["base_solar_kw"] * (1 + random.uniform(-0.01, 0.015))
    occupancy = max(0, TELEMETRY_STATE["base_occupancy"] + random.randint(-8, 12))
    detail = None
    if mode == "energy_spike":
        energy *= 1.35
        detail = {"type": "energy", "facility_id": "academic-research", "message": "Simulated load increase above demo baseline."}
    elif mode == "water_leak":
        water *= 1.72
        detail = {"type": "water", "facility_id": "library", "message": "Simulated water-flow increase above demo baseline."}
    elif mode == "waste_overflow":
        detail = {"type": "waste", "facility_id": None, "message": "Simulated overflow observation; location unverified."}
    # These shares are illustrative allocations of campus-wide demo totals. They
    # are not facility meter readings or surveyed sensor locations.
    weights = {
        "academic-research": (0.30, 0.24, 0.32),
        "library": (0.15, 0.10, 0.12),
        "innovation-maker": (0.22, 0.22, 0.19),
        "sports-fitness": (0.08, 0.13, 0.12),
        "medical-campus": (0.25, 0.31, 0.25),
    }
    facility_metrics = {
        facility_id: {
            "energy_kw": round(energy * share[0] * random.uniform(0.97, 1.03), 1),
            "water_lps": round(water * share[1] * random.uniform(0.97, 1.03), 3),
            "occupancy": round(occupancy * share[2] * random.uniform(0.97, 1.03)),
            "allocation_only": True,
        }
        for facility_id, share in weights.items()
    }
    facility_metrics["solar-infrastructure"] = {
        "solar_generation_kw": round(solar, 1), "allocation_only": True
    }
    timestamp = datetime.now().isoformat(timespec="seconds")
    TELEMETRY_STATE["history"].append({
        "timestamp": timestamp, "energy_kw": round(energy, 1),
        "water_lps": round(water, 3), "solar_generation_kw": round(solar, 1),
        "campus_occupancy": occupancy, "simulation_mode": mode,
    })
    TELEMETRY_STATE["history"] = TELEMETRY_STATE["history"][-60:]
    return jsonify({
        "success": True, "is_simulated": True, "data_source": "DEMO_SIMULATOR",
        "source_label": "Simulated values · no physical sensors connected",
        "timestamp": timestamp, "simulation_mode": mode,
        "metrics": {"energy_kw": round(energy, 1), "water_lps": round(water, 2),
                    "solar_generation_kw": round(solar, 1), "campus_occupancy": occupancy},
        "facility_metrics": facility_metrics,
        "history": TELEMETRY_STATE["history"],
        "history_limit": 60,
        "anomaly": {"is_active": detail is not None, "detail": detail},
        "recent_events": TELEMETRY_STATE["events"][-6:]
    }), 200


@app.route("/api/telemetry/simulate-anomaly", methods=["POST"])
def simulate_anomaly():
    data = request.get_json(silent=True) or {}
    anomaly_type = data.get("type", "reset")
    if anomaly_type not in ["energy_spike", "water_leak", "waste_overflow", "reset"]:
        return jsonify({"success": False, "message": "Invalid demo scenario."}), 400
    TELEMETRY_STATE["simulation_mode"] = anomaly_type
    timestamp = datetime.now().strftime("%H:%M:%S")
    if anomaly_type == "reset":
        message, category = "Demo readings reset; physical sensor state is unknown.", "system"
    else:
        scenario = SIMULATION_SCENARIOS[anomaly_type]
        message, category = f"DEMO SCENARIO: {scenario['title']}", scenario["category"].lower()
    TELEMETRY_STATE["events"].append({"time": timestamp, "category": category, "text": message})
    TELEMETRY_STATE["events"] = TELEMETRY_STATE["events"][-100:]

    connection = get_db()
    cursor = connection.cursor()
    if anomaly_type == "reset":
        cursor.execute("""
            UPDATE alerts SET status='Completed', notes='Demo scenario reset; this was not a physical incident.'
            WHERE source='Demo Simulation' AND status!='Completed'
        """)
    elif anomaly_type in SIMULATION_SCENARIOS:
        scenario = SIMULATION_SCENARIOS[anomaly_type]
        existing = cursor.execute(
            "SELECT id FROM alerts WHERE source='Demo Simulation' AND title=? AND status!='Completed' LIMIT 1",
            (scenario["title"],)
        ).fetchone()
        if existing is None:
            facility_id = scenario["facility_id"]
            location = DSU_FACILITIES[facility_id]["name"] if facility_id else "Campus-wide / location unverified"
            cursor.execute("""
                INSERT INTO alerts (title,category,location,priority,evidence,action,status,created_at,source,
                    impact_estimate,facility_id,assignee,sla_hours)
                VALUES (?,?,?,?,?,?,'Open',?,'Demo Simulation',?,?,?,?)
            """, (
                scenario["title"], scenario["category"], location, scenario["priority"],
                f"Simulated event only. {message} No physical sensor or asset confirmation is available.",
                scenario["action"], datetime.now().strftime("%Y-%m-%d %H:%M"),
                "No verified environmental savings; demo scenario only.", facility_id, scenario["assignee"], scenario["sla_hours"]
            ))
    connection.commit()
    connection.close()
    return jsonify({"success": True, "is_simulated": True, "simulation_mode": anomaly_type, "message": message, "timestamp": timestamp}), 200


@app.route("/api/telemetry/upload-csv", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No CSV file uploaded."}), 400
    filename = Path(request.files["file"].filename or "").name
    if not filename.lower().endswith(".csv"):
        return jsonify({"success": False, "message": "Please upload a valid .csv spreadsheet."}), 400
    try:
        reader = csv.DictReader(io.StringIO(request.files["file"].read().decode("utf-8-sig")))
        if not reader.fieldnames:
            return jsonify({"success": False, "message": "CSV must include a header row."}), 400
        fields = {name.strip().lower(): name for name in reader.fieldnames if name}
        timestamp_field = next((fields[key] for key in ("timestamp", "time", "date", "datetime", "measured_at") if key in fields), None)
        id_field = fields.get("facility_id")
        facility_field = next((fields[key] for key in ("facility", "building", "location") if key in fields), None)
        metric_field = next((fields[key] for key in ("metric", "measurement", "type") if key in fields), None)
        unit_field = fields.get("unit")
        value_field = next((fields[key] for key in ("value", "reading", "consumption") if key in fields), None)
        wide_columns = {
            "kwh": ("energy", "kWh"), "energy_kwh": ("energy", "kWh"), "energy": ("energy", "kWh"),
            "liters": ("water", "L"), "litres": ("water", "L"), "water_liters": ("water", "L"),
            "water_litres": ("water", "L"), "water_l": ("water", "L"),
            "waste_kg": ("waste", "kg"), "waste_diverted_kg": ("waste", "kg")
        }
        aliases = {
            "kwh": ("energy", "kWh"), "energy": ("energy", "kWh"), "electricity": ("energy", "kWh"),
            "water": ("water", "L"), "liter": ("water", "L"), "liters": ("water", "L"),
            "litre": ("water", "L"), "litres": ("water", "L"), "l": ("water", "L"),
            "waste": ("waste", "kg"), "waste_kg": ("waste", "kg"), "kg": ("waste", "kg")
        }
        name_to_id = {value["name"].casefold(): key for key, value in DSU_FACILITIES.items()}
        records = []
        for row in reader:
            label = (row.get(facility_field) or "").strip() if facility_field else ""
            raw_id = (row.get(id_field) or "").strip() if id_field else ""
            facility_id = raw_id if raw_id in DSU_FACILITIES else name_to_id.get(label.casefold())
            measured_at = (row.get(timestamp_field) or "").strip() if timestamp_field else ""
            if not measured_at:
                measured_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row_values = []
            if value_field:
                raw_metric = (row.get(metric_field) or "").strip().lower() if metric_field else ""
                declared_unit = (row.get(unit_field) or "").strip() if unit_field else ""
                metric, unit = aliases.get(raw_metric, (None, None))
                if metric is None and declared_unit:
                    metric, unit = aliases.get(declared_unit.lower(), (None, None))
                if metric:
                    row_values.append((metric, declared_unit or unit, row.get(value_field)))
            else:
                for column, (metric, unit) in wide_columns.items():
                    source_column = fields.get(column)
                    if source_column and row.get(source_column) not in (None, ""):
                        row_values.append((metric, unit, row.get(source_column)))
            for metric, unit, raw_value in row_values:
                try:
                    value = float(str(raw_value).strip())
                except (TypeError, ValueError):
                    continue
                if math.isfinite(value) and value >= 0:
                    records.append({
                        "facility_id": facility_id,
                        "facility_label": label or (DSU_FACILITIES[facility_id]["name"] if facility_id else "Unverified facility"),
                        "metric": metric, "value": value, "unit": unit, "measured_at": measured_at
                    })
        if not records:
            return jsonify({"success": False, "message": "No valid energy, water, or waste readings found."}), 400

        groups = {}
        for record in records:
            key = (record["facility_id"] or record["facility_label"].casefold(), record["metric"])
            groups.setdefault(key, []).append(record)
        stats = {}
        for key, group in groups.items():
            mean = sum(item["value"] for item in group) / len(group)
            stats[key] = {"mean": mean, "threshold": mean * 1.25}
        anomalies = []
        for record in records:
            key = (record["facility_id"] or record["facility_label"].casefold(), record["metric"])
            record["is_anomaly"] = record["value"] > stats[key]["threshold"]
            if record["is_anomaly"]:
                anomalies.append(record)

        imported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO meter_imports (filename,imported_at,reading_count) VALUES (?,?,?)", (filename, imported_at, len(records)))
        import_id = cursor.lastrowid
        cursor.executemany("""
            INSERT INTO meter_readings (import_id,facility_id,facility_label,metric,value,unit,measured_at,is_anomaly)
            VALUES (?,?,?,?,?,?,?,?)
        """, [(import_id, item["facility_id"], item["facility_label"], item["metric"], item["value"], item["unit"], item["measured_at"], int(item["is_anomaly"])) for item in records])
        connection.commit()
        connection.close()
        metric_stats = [{
            "metric": group[0]["metric"], "facility_id": group[0]["facility_id"], "facility": group[0]["facility_label"],
            "unit": group[0]["unit"], "count": len(group), "mean": round(stats[key]["mean"], 3),
            "peak": round(max(item["value"] for item in group), 3), "threshold": round(stats[key]["threshold"], 3)
        } for key, group in groups.items()]
        return jsonify({
            "success": True, "import_id": import_id, "filename": filename, "imported_at": imported_at,
            "data_source": "User-uploaded CSV; historical readings, not live", "total_records": len(records),
            "anomalies_detected": len(anomalies), "metrics": metric_stats, "anomaly_points": anomalies[:20],
            "message": f"Stored {len(records)} historical readings. Flagged {len(anomalies)} values above 1.25x their facility/metric mean."
        }), 200
    except (UnicodeDecodeError, csv.Error) as error:
        return jsonify({"success": False, "message": f"Could not parse CSV: {error}"}), 400


@app.route("/api/telemetry/readings", methods=["GET"])
def get_meter_readings():
    connection = get_db()
    rows = connection.execute("""
        SELECT reading.id, reading.import_id, reading.facility_id, reading.facility_label,
            reading.metric, reading.value, reading.unit, reading.measured_at, reading.is_anomaly,
            imported.filename, imported.imported_at
        FROM meter_readings AS reading
        JOIN meter_imports AS imported ON imported.id = reading.import_id
        ORDER BY imported.imported_at DESC, reading.id DESC
    """).fetchall()
    connection.close()
    return jsonify({"success": True, "count": len(rows), "readings": [dict(row) for row in rows]}), 200


@app.route("/api/campus-data", methods=["GET"])
def campus_data():
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id,title,category,location,priority,evidence,action,status,created_at,source,
            facility_id,assignee,notes,sla_hours FROM alerts ORDER BY created_at DESC,id DESC
    """)
    alerts = [dict(row) for row in cursor.fetchall()]
    cursor.execute("""
        SELECT reading.facility_id,reading.metric,reading.value,reading.unit,reading.measured_at,
            reading.is_anomaly,imported.filename
        FROM meter_readings AS reading JOIN meter_imports AS imported ON imported.id=reading.import_id
        WHERE reading.facility_id IS NOT NULL ORDER BY imported.imported_at DESC,reading.id DESC
    """)
    readings = [dict(row) for row in cursor.fetchall()]
    connection.close()

    facilities = []
    for facility_id, reference in DSU_FACILITIES.items():
        facility_alerts = [alert for alert in alerts if alert.get("facility_id") == facility_id]
        active_alerts = [alert for alert in facility_alerts if alert["status"] != "Completed"]
        latest = {}
        for reading in readings:
            if reading["facility_id"] == facility_id and reading["metric"] not in latest:
                latest[reading["metric"]] = reading
        anomaly = any(row["is_anomaly"] for row in latest.values())
        if any(alert["priority"] == "High" for alert in active_alerts) or anomaly:
            status, status_label = "alert", "Attention required"
        elif active_alerts:
            status, status_label = "attention", "Open work order"
        elif latest:
            status, status_label = "normal", "CSV readings available; not live"
        else:
            status, status_label = "unknown", "No live data source"
        files = sorted({row["filename"] for row in latest.values()})
        facilities.append({
            "id": facility_id, "name": reference["name"], "description": reference["description"],
            "source_pages": reference["source_pages"], "source_url": BROCHURE_URL,
            "status": status, "status_label": status_label,
            "telemetry": {
                "energy": latest.get("energy"), "water": latest.get("water"), "waste": latest.get("waste"),
                "data_source": ", ".join(files) if files else None,
                "last_updated": max((row["measured_at"] for row in latest.values()), default=None)
            },
            "alerts": facility_alerts[:5]
        })
    return jsonify({
        "success": True,
        "campus": {"name": "Dayananda Sagar University", "address": "Devarakaggalahalli, Harohalli, Kanakapura Road, Karnataka", "reference": BROCHURE_URL},
        "map_type": "illustrative_schematic_not_to_scale", "map_positions_verified": False,
        "telemetry_available": bool(readings), "telemetry_note": "CSV readings are historical uploads, not a live sensor stream.",
        "facilities": facilities
    }), 200


@app.route("/api/detect-waste", methods=["POST"])
def detect_waste():
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No image file provided."}), 400
    uploaded_file = request.files["image"]
    if not uploaded_file.filename:
        return jsonify({"success": False, "message": "No file was selected."}), 400
    try:
        image = Image.open(io.BytesIO(uploaded_file.read())).convert("RGB")
    except (UnidentifiedImageError, OSError):
        return jsonify({"success": False, "message": "Invalid or corrupt image."}), 400
    try:
        result = model.predict(source=image, conf=0.25, imgsz=640, verbose=False)[0]
        detections = []
        waste_stats = {"recyclable": 0, "organic": 0, "packaging": 0, "other": 0}
        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                label = model.names[class_id]
                category, display_name = "other", label.capitalize()
                for group, mapping in WASTE_CATEGORIES.items():
                    if label in mapping:
                        category, display_name = group, mapping[label]
                        break
                waste_stats[category] += 1
                detections.append({
                    "label": label, "display_name": display_name, "confidence": round(confidence * 100, 1),
                    "possible_waste_related": label in ALL_WASTE_LABELS, "category": category,
                    "box": [round(float(value), 1) for value in box.xyxy[0].tolist()]
                })
        waste_count = sum(item["possible_waste_related"] for item in detections)
        latest = "latest_detection.jpg"
        result.save(filename=str(STATIC_DIR / latest))
        result.save(filename=str(DETECTIONS_DIR / f"detection_{int(time.time())}.jpg"))
        message = f"Detected {waste_count} potentially waste-related item(s). Review before dispatch." if waste_count else "No obvious waste-related objects detected."
        return jsonify({
            "success": True, "model": "YOLOv8n Pretrained COCO Object Detector",
            "total_objects": len(detections), "possible_waste_related_count": waste_count,
            "waste_breakdown": waste_stats, "detections": detections,
            "annotated_image": f"/static/{latest}", "message": message,
            "limitation": "COCO detects general objects, not intent. Human confirmation is required."
        }), 200
    except Exception as error:
        app.logger.exception("Inference error")
        return jsonify({"success": False, "message": f"AI detection failed: {error}"}), 500


@app.route("/api/financial-impact", methods=["GET"])
def financial_impact():
    connection = get_db()
    rows = connection.execute("""
        SELECT status,energy_savings_kwh,water_savings_liters,waste_diverted_kg
        FROM alerts WHERE status='Completed'
    """).fetchall()
    total = connection.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    connection.close()
    energy = sum(float(row["energy_savings_kwh"] or 0) for row in rows)
    water = sum(float(row["water_savings_liters"] or 0) for row in rows)
    waste = sum(float(row["waste_diverted_kg"] or 0) for row in rows)
    co2 = round(energy * 0.82, 2)
    usd_energy, inr_energy = round(energy * 0.14, 2), round(energy * 8.5, 2)
    usd_water, inr_water = round(water * 0.004, 2), round(water * 0.25, 2)
    completed = len(rows)
    return jsonify({
        "success": True,
        "summary": {"total_tickets": total, "resolved_tickets": completed, "resolution_rate_pct": round(completed / max(1, total) * 100, 1)},
        "environmental_esg": {
            "electricity_saved_kwh": round(energy, 2), "water_conserved_liters": round(water, 2),
            "waste_diverted_landfill_kg": round(waste, 2), "ghg_co2e_avoided_kg": co2,
            "trees_equivalent_annual": round(co2 / 21.77, 2)
        },
        "financial_cost_avoidance": {
            "usd": {"energy_savings": usd_energy, "water_savings": usd_water, "total_savings": round(usd_energy + usd_water, 2), "currency_symbol": "$"},
            "inr": {"energy_savings": inr_energy, "water_savings": inr_water, "total_savings": round(inr_energy + inr_water, 2), "currency_symbol": "₹"}
        },
        "provenance": "Estimates entered on completed work orders; not independently verified against utility bills."
    }), 200


@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    category, status, search = request.args.get("category"), request.args.get("status"), request.args.get("search")
    query, params = "SELECT * FROM alerts WHERE 1=1", []
    if category and category.lower() != "all":
        query += " AND LOWER(category)=LOWER(?)"
        params.append(category)
    if status and status.lower() != "all":
        query += " AND LOWER(status)=LOWER(?)"
        params.append(status)
    if search:
        query += " AND (LOWER(title) LIKE ? OR LOWER(location) LIKE ? OR LOWER(evidence) LIKE ? OR LOWER(assignee) LIKE ?)"
        term = f"%{search.lower()}%"
        params.extend([term, term, term, term])
    query += " ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,id DESC"
    connection = get_db()
    alerts = [add_sla_details(dict(row)) for row in connection.execute(query, params).fetchall()]
    connection.close()
    return jsonify({"success": True, "count": len(alerts), "alerts": alerts}), 200


@app.route("/api/alerts", methods=["POST"])
def create_alert():
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data.get("title") or not data.get("location"):
        return jsonify({"success": False, "message": "Title and location are required."}), 400
    category = data.get("category", "Waste")
    priority, status = data.get("priority", "Medium"), data.get("status", "Open")
    facility_id = data.get("facility_id")
    facility_id = facility_id if facility_id in DSU_FACILITIES else None
    assignee = data.get("assignee", "Facility Crew Alpha")
    try:
        sla = int(data.get("sla_hours", 4))
        estimates = [float(data.get(key, 0)) for key in ("energy_savings_kwh", "water_savings_liters", "waste_diverted_kg")]
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "SLA and savings estimates must be numeric."}), 400
    if category not in {"Waste", "Energy", "Water"} or priority not in {"High", "Medium", "Low"} or status not in {"Open", "In Progress", "Completed"}:
        return jsonify({"success": False, "message": "Category, priority, or status is invalid."}), 400
    if assignee not in CREWS or not 1 <= sla <= 720 or any(not math.isfinite(value) or value < 0 for value in estimates):
        return jsonify({"success": False, "message": "Crew, SLA, or savings estimate is invalid."}), 400
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO alerts (title,category,location,priority,evidence,action,status,created_at,source,impact_estimate,
            facility_id,assignee,notes,sla_hours,energy_savings_kwh,water_savings_liters,waste_diverted_kg)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["title"].strip(), category, data["location"], priority,
        data.get("evidence", "Manual observation; details not provided."),
        data.get("action", "Inspect and document corrective action."), status,
        datetime.now().strftime("%Y-%m-%d %H:%M"), data.get("source", "Manual Inspection"),
        "User-entered estimate; not verified." if any(estimates) else None,
        facility_id, assignee, data.get("notes", ""), sla, *estimates
    ))
    alert_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return jsonify({"success": True, "alert_id": alert_id, "message": "Work order created."}), 201


@app.route("/api/alerts/<int:alert_id>", methods=["PATCH"])
def update_alert(alert_id):
    data = request.get_json(silent=True) or {}
    connection = get_db()
    cursor = connection.cursor()
    existing = cursor.execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone()
    if existing is None:
        connection.close()
        return jsonify({"success": False, "message": "Work order not found."}), 404
    status = data.get("status", existing["status"])
    priority = data.get("priority", existing["priority"])
    assignee = data.get("assignee", existing["assignee"])
    notes = data.get("notes", existing["notes"])
    if status not in {"Open", "In Progress", "Completed"} or priority not in {"High", "Medium", "Low"} or assignee not in CREWS:
        connection.close()
        return jsonify({"success": False, "message": "Status, priority, or crew is invalid."}), 400
    if status == "Completed" and not str(notes or "").strip():
        connection.close()
        return jsonify({"success": False, "message": "Resolution notes are required to complete a work order."}), 400
    cursor.execute("UPDATE alerts SET status=?,priority=?,assignee=?,notes=? WHERE id=?", (status, priority, assignee, notes, alert_id))
    connection.commit()
    connection.close()
    return jsonify({"success": True, "alert": {"id": alert_id, "status": status, "priority": priority, "assignee": assignee, "notes": notes}}), 200


@app.route("/api/alerts/<int:alert_id>", methods=["DELETE"])
def delete_alert(alert_id):
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
    affected = cursor.rowcount
    connection.commit()
    connection.close()
    if not affected:
        return jsonify({"success": False, "message": "Work order not found."}), 404
    return jsonify({"success": True, "message": f"Work order #{alert_id} deleted."}), 200


# -------------------------------------------------------------
# Database Inspector & Export Endpoints
# -------------------------------------------------------------
@app.route("/api/database/overview", methods=["GET"])
def database_overview():
    """Returns database metadata, tables, schema, and live record counts."""
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables_meta = []
    
    for row in cursor.fetchall():
        table_name = row["name"]
        cursor.execute(f"PRAGMA table_info({table_name});")
        cols = [{"name": c["name"], "type": c["type"], "pk": bool(c["pk"])} for c in cursor.fetchall()]
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
        row_count = cursor.fetchone()["count"]
        tables_meta.append({
            "name": table_name,
            "row_count": row_count,
            "columns": cols
        })
    connection.close()

    db_size = os.path.getsize(DB_PATH) if DB_PATH.exists() else 0
    return jsonify({
        "success": True,
        "database": "campus.db",
        "engine": "SQLite 3",
        "size_kb": round(db_size / 1024, 2),
        "total_tables": len(tables_meta),
        "tables": tables_meta
    }), 200


@app.route("/api/database/table/<table_name>", methods=["GET"])
def database_table_data(table_name):
    """Returns rows and columns from a specific SQLite table."""
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    if not cursor.fetchone():
        connection.close()
        return jsonify({"success": False, "message": f"Table '{table_name}' does not exist."}), 404

    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [c["name"] for c in cursor.fetchall()]
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 100;")
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.execute(f"SELECT COUNT(*) as total FROM {table_name};")
    total_count = cursor.fetchone()["total"]
    connection.close()

    return jsonify({
        "success": True,
        "table": table_name,
        "columns": columns,
        "total_count": total_count,
        "returned_count": len(rows),
        "rows": rows
    }), 200


@app.route("/api/database/download", methods=["GET"])
def download_database_file():
    """Allows downloading the raw campus.db SQLite file directly."""
    if not DB_PATH.exists():
        return jsonify({"success": False, "message": "Database file not found."}), 404
    return send_from_directory(BACKEND_DIR, "campus.db", as_attachment=True, download_name="campus.db")


@app.route("/api/database/schema-sql", methods=["GET"])
def download_schema_sql():
    """Returns the SQL schema file for documentation and reproduction."""
    schema_path = BACKEND_DIR / "schema.sql"
    if not schema_path.exists():
        return jsonify({"success": False, "message": "schema.sql not found."}), 404
    return send_from_directory(BACKEND_DIR, "schema.sql", as_attachment=True, download_name="schema.sql")


@app.route("/api/database/seed-sql", methods=["GET"])
def download_seed_sql():
    """Returns the SQL seed file."""
    seed_path = BACKEND_DIR / "seed.sql"
    if not seed_path.exists():
        return jsonify({"success": False, "message": "seed.sql not found."}), 404
    return send_from_directory(BACKEND_DIR, "seed.sql", as_attachment=True, download_name="seed.sql")


@app.errorhandler(400)
def handle_bad_request(error):
    return jsonify({"success": False, "message": getattr(error, "description", "Bad request.")}), 400


@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({"success": False, "message": "Endpoint not found."}), 404


@app.errorhandler(413)
def handle_too_large(error):
    return jsonify({"success": False, "message": "Upload exceeds the 8 MB limit."}), 413


@app.errorhandler(500)
def handle_server_error(error):
    return jsonify({"success": False, "message": "Internal server error. Check the Flask log."}), 500


if __name__ == "__main__":
    print("[EcoCampus AI] Starting Flask on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
