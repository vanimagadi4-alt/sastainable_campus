"""
EcoNova AI — Intelligent Digital Twin for Sustainable Campuses
Database Management Module
Dayananda Sagar University (DSU), Harohalli Campus

Provides SQLite database initialization, automated schema migration,
realistic seed data, and query interfaces.
"""

import os
import sqlite3
from datetime import datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecotwin.db")

import os
import sqlite3
from datetime import datetime, timedelta

DB_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ecowin.db"
)

def get_db_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_connection():
    """Returns a connection to the SQLite database with dictionary-like row access."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force_reseed=False):
    """Initializes tables and seeds initial realistic demo data for DSU Harohalli."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables as defined in requirements
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(30) DEFAULT 'Student',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS energy_consumption (
        energy_id INTEGER PRIMARY KEY AUTOINCREMENT,
        building_name VARCHAR(100) NOT NULL,
        energy_used DECIMAL(10,2) NOT NULL,
        solar_energy DECIMAL(10,2) DEFAULT 0,
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS water_consumption (
        water_id INTEGER PRIMARY KEY AUTOINCREMENT,
        building_name VARCHAR(100) NOT NULL,
        water_used DECIMAL(10,2) NOT NULL,
        water_recycled DECIMAL(10,2) DEFAULT 0,
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS waste_management (
        waste_id INTEGER PRIMARY KEY AUTOINCREMENT,
        waste_type VARCHAR(50) NOT NULL,
        quantity_kg DECIMAL(10,2) NOT NULL,
        disposal_method VARCHAR(50),
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS air_quality (
        air_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location VARCHAR(100) NOT NULL,
        co2_level DECIMAL(10,2),
        pm25_level DECIMAL(10,2),
        temperature DECIMAL(5,2),
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sustainability_recommendations (
        recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category VARCHAR(50) NOT NULL,
        recommendation TEXT NOT NULL,
        priority VARCHAR(20) DEFAULT 'Medium',
        status VARCHAR(30) DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS carbon_emissions (
        emission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source VARCHAR(100) NOT NULL,
        activity_value DECIMAL(10,2) NOT NULL,
        emission_factor DECIMAL(10,4) NOT NULL,
        co2_equivalent_kg DECIMAL(12,2) NOT NULL,
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sustainability_actions (
        action_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INT,
        activity_name VARCHAR(100) NOT NULL,
        points INT DEFAULT 0,
        activity_date DATE,
        verification_status VARCHAR(30) DEFAULT 'Pending',
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(150) NOT NULL,
        facility VARCHAR(100) NOT NULL,
        category VARCHAR(50) NOT NULL,
        severity VARCHAR(20) NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        description TEXT NOT NULL,
        recommended_action TEXT NOT NULL,
        status VARCHAR(30) DEFAULT 'Active'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS waste_detections (
        detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_name VARCHAR(255),
        detected_objects TEXT,
        confidence_score DECIMAL(5,2),
        classified_category VARCHAR(50),
        recyclable_status VARCHAR(50),
        carbon_offset_kg DECIMAL(6,2),
        model_used VARCHAR(50),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    # Check if seed data exists
    cursor.execute("SELECT COUNT(*) FROM energy_consumption")
    count = cursor.fetchone()[0]

    if count == 0 or force_reseed:
        seed_demo_data(conn)

    conn.close()


def seed_demo_data(conn):
    """Populates realistic demo metrics for DSU Harohalli Campus."""
    cursor = conn.cursor()

    # 1. Users
    users_data = [
        ("Campus Admin", "admin@dsu.edu.in", "admin_hash_dsu", "Administrator"),
        ("Sustainability Officer", "eco@dsu.edu.in", "eco_hash_dsu", "Staff"),
        ("Student Volunteer", "student@dsu.edu.in", "stu_hash_dsu", "Student"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        users_data
    )

    # Buildings in DSU Harohalli
    buildings = [
        "Engineering Complex (Block A)",
        "Computer Science & AI Center (Block B)",
        "Central Library & Innovation Hub",
        "Biotech & Life Sciences Research Labs",
        "Central Cafeteria & Food Court",
        "Student Hostels (Kaveri & Sharavathi Blocks)",
        "Sports Complex & Gymnasium",
        "Administrative & VC Pavilion"
    ]

    # 2. Energy Consumption (Last 7 days of demo readings)
    now = datetime.now()
    energy_records = []
    base_kwh = {
        "Engineering Complex (Block A)": (480, 160),
        "Computer Science & AI Center (Block B)": (550, 190),
        "Central Library & Innovation Hub": (210, 80),
        "Biotech & Life Sciences Research Labs": (420, 110),
        "Central Cafeteria & Food Court": (280, 60),
        "Student Hostels (Kaveri & Sharavathi Blocks)": (390, 75),
        "Sports Complex & Gymnasium": (140, 45),
        "Administrative & VC Pavilion": (180, 50)
    }

    for days_back in range(7, -1, -1):
        dt = (now - timedelta(days=days_back)).strftime("%Y-%m-%d 14:00:00")
        for b_name, (grid, solar) in base_kwh.items():
            variation = (days_back % 3 - 1) * 15
            used = max(50.0, grid + variation)
            sol = max(10.0, solar + (days_back % 2) * 12)
            energy_records.append((b_name, round(used, 2), round(sol, 2), dt))

    cursor.executemany(
        "INSERT INTO energy_consumption (building_name, energy_used, solar_energy, recorded_at) VALUES (?, ?, ?, ?)",
        energy_records
    )

    # 3. Water Consumption (Last 7 days)
    water_records = []
    base_liters = {
        "Engineering Complex (Block A)": (3200, 1200),
        "Computer Science & AI Center (Block B)": (3800, 1400),
        "Central Library & Innovation Hub": (1100, 400),
        "Biotech & Life Sciences Research Labs": (5400, 800), # Higher for lab research
        "Central Cafeteria & Food Court": (6200, 2200), # High kitchen usage
        "Student Hostels (Kaveri & Sharavathi Blocks)": (9800, 3900), # Living quarters
        "Sports Complex & Gymnasium": (2100, 700),
        "Administrative & VC Pavilion": (900, 350)
    }

    for days_back in range(7, -1, -1):
        dt = (now - timedelta(days=days_back)).strftime("%Y-%m-%d 17:00:00")
        for b_name, (used_l, rec_l) in base_liters.items():
            var = (days_back % 4 - 2) * 80
            used = round(max(300.0, used_l + var), 2)
            recycled = round(max(50.0, rec_l + var * 0.3), 2)
            water_records.append((b_name, used, recycled, dt))

    cursor.executemany(
        "INSERT INTO water_consumption (building_name, water_used, water_recycled, recorded_at) VALUES (?, ?, ?, ?)",
        water_records
    )

    # 4. Waste Management Records
    waste_records = [
        ("Organic Food Waste", 485.50, "Biomethanation & Composting Plant", (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PET Bottles & Plastic", 192.30, "Authorized Recycler (Harohalli Industrial Hub)", (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
        ("Paper & Cardboard", 260.00, "Campus Paper Reprocessing Unit", (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),
        ("E-Waste & Computer Components", 42.10, "Certified E-Waste Dismantler", (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")),
        ("Glass & Metals", 68.40, "Material Recovery Facility", (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")),
        ("Laboratory Chemical Neutralized Waste", 31.20, "Secured Hazardous Facility", (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")),
    ]
    cursor.executemany(
        "INSERT INTO waste_management (waste_type, quantity_kg, disposal_method, recorded_at) VALUES (?, ?, ?, ?)",
        waste_records
    )

    # 5. Air Quality Records
    air_records = [
        ("Engineering Complex Courtyard", 418.5, 28.2, 26.4),
        ("Computer Science & AI Server Zone", 535.0, 18.5, 22.1),
        ("Central Library Reading Atrium", 440.0, 15.0, 24.0),
        ("Harohalli Gate Entrance (Traffic)", 612.0, 48.6, 28.5),
        ("Sports Complex Field", 395.0, 22.0, 27.2),
        ("Hostel Lake Promenade", 388.0, 14.2, 25.0)
    ]
    cursor.executemany(
        "INSERT INTO air_quality (location, co2_level, pm25_level, temperature) VALUES (?, ?, ?, ?)",
        air_records
    )

    # 6. Sustainability Recommendations
    rec_records = [
        ("Energy", "Schedule HVAC power cycles in Block A lecture halls based on student timetable gaps to cut baseline grid usage by 18%.", "High", "Pending"),
        ("Water", "Install automated solenoid shutoff valves on Biotech Lab secondary wash lines to resolve persistent off-hour pressure drops.", "High", "In Review"),
        ("Waste", "Deploy multimodal AI waste classification kiosks at Central Cafeteria exits to reduce food contamination in dry recycling bins.", "Medium", "Approved"),
        ("Renewable", "Expand rooftop solar PV capacity on Library Building to offset nighttime server room compute loads.", "Medium", "Pending"),
        ("Carbon", "Incentivize Harohalli campus electric shuttle pooling among faculty and day scholars to lower Scope 3 transport footprint.", "Low", "Approved")
    ]
    cursor.executemany(
        "INSERT INTO sustainability_recommendations (category, recommendation, priority, status) VALUES (?, ?, ?, ?)",
        rec_records
    )

    # 7. Carbon Emissions
    carbon_records = [
        ("Grid Electricity (BESCOM)", 2840.00, 0.8200, 2328.80),
        ("Diesel Backup Generators (DG Set)", 140.00, 2.6800, 375.20),
        ("Campus Bus Fleet & Transport", 410.00, 1.4500, 594.50),
        ("Cafeteria Commercial LPG", 220.00, 1.5100, 332.20),
        ("Biomass & Food Decomp (Offset Credit)", -320.00, 1.2000, -384.00)
    ]
    cursor.executemany(
        "INSERT INTO carbon_emissions (source, activity_value, emission_factor, co2_equivalent_kg) VALUES (?, ?, ?, ?)",
        carbon_records
    )

    # 8. Alerts (Priority Action Center)
    alert_records = [
        ("Unusual Water Flow Rate Detected", "Biotech & Life Sciences Research Labs", "Water", "Critical",
         (now - timedelta(hours=2, minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
         "Secondary cooling line flow sensor #W-BIO-04 recorded an anomalous 18.4 L/min sustained flow during zero-occupancy hours.",
         "Deploy facility maintenance team to inspect valve manifold #4B and activate digital twin isolation bypass.", "Active"),

        ("Peak Solar Generation Inverter Limit", "Engineering Complex (Block A)", "Energy", "Warning",
         (now - timedelta(hours=4, minutes=40)).strftime("%Y-%m-%d %H:%M:%S"),
         "Rooftop Solar Array PV-02 reached 96% inverter rated threshold due to intense noon irradiance.",
         "Verify inverter cooling fans and check export load balancing to the central campus substation.", "Active"),

        ("Cafeteria Wet Waste Segregation Alert", "Central Cafeteria & Food Court", "Waste", "Warning",
         (now - timedelta(hours=6, minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
         "AI vision camera over bin cluster C-3 flagged high cross-contamination of plastic cutlery inside organic compost bins.",
         "Broadcast audio segregation reminder at tray return and alert housekeeping supervisor.", "Acknowledged"),

        ("Central Rainwater Reservoir Buffer Healthy", "Water Treatment & Rainwater Lake", "Water", "Info",
         (now - timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S"),
         "Monsoon catchment basin capacity reached 88% full; greywater recycling plant operating at optimal 4,200 L/hr yield.",
         "Log monthly water resilience score and ensure overflow drains to secondary percolation pit.", "Resolved"),

        ("Elevated CO2 in Server Room", "Computer Science & AI Center (Block B)", "Energy", "Warning",
         (now - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S"),
         "CO2 levels reached 535 ppm with server rack thermal rise to 25.4 C during scheduled model training workloads.",
         "Modulate AHU damper to 35% fresh air intake and optimize rack airflow baffles.", "Acknowledged")
    ]

    cursor.executemany(
        "INSERT INTO alerts (title, facility, category, severity, timestamp, description, recommended_action, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        alert_records
    )

    # Demo detections
    detections = [
        ("demo_can.jpg", "Crushed Aluminum Beverage Can", 0.94, "Recyclable (Metal)", "Recyclable", 0.42, "YOLOv8 Demo"),
        ("demo_bottle.jpg", "PET Plastic Drinking Water Bottle", 0.89, "Recyclable (Plastic)", "Recyclable", 0.28, "YOLOv8 Demo"),
        ("demo_banana.jpg", "Organic Fruit Waste / Peel", 0.96, "Biodegradable (Compost)", "Compostable", 0.15, "YOLOv8 Demo")
    ]
    cursor.executemany(
        "INSERT INTO waste_detections (image_name, detected_objects, confidence_score, classified_category, recyclable_status, carbon_offset_kg, model_used) VALUES (?, ?, ?, ?, ?, ?, ?)",
        detections
    )

    conn.commit()


# Helper query functions

def get_overview_metrics():
    """Calculates top-level KPI metrics for the overview dashboard."""
    conn = get_db_connection()
    c = conn.cursor()

    # Total energy used and solar
    c.execute("SELECT SUM(energy_used), SUM(solar_energy) FROM energy_consumption WHERE recorded_at >= date('now', '-7 days')")
    row = c.fetchone()
    total_energy = round(row[0] or 0.0, 1)
    total_solar = round(row[1] or 0.0, 1)

    # Total water used and recycled
    c.execute("SELECT SUM(water_used), SUM(water_recycled) FROM water_consumption WHERE recorded_at >= date('now', '-7 days')")
    row = c.fetchone()
    total_water = round(row[0] or 0.0, 1)
    total_recycled_water = round(row[1] or 0.0, 1)

    # Total waste collected
    c.execute("SELECT SUM(quantity_kg) FROM waste_management")
    row = c.fetchone()
    total_waste = round(row[0] or 0.0, 1)

    # Waste detections analyzed
    c.execute("SELECT COUNT(*) FROM waste_detections")
    waste_scans = c.fetchone()[0]

    # Active alerts count
    c.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Active'")
    active_alerts = c.fetchone()[0]

    # Carbon savings estimate (solar offset + recycling offset)
    # Solar saves ~0.82 kg CO2 per kWh; recycling saves ~1.5 kg CO2 per kg
    solar_carbon_saved = total_solar * 0.82
    recycled_carbon_saved = (total_waste * 0.6) * 1.2
    carbon_saved_kg = round(solar_carbon_saved + recycled_carbon_saved, 1)

    # Sustainability score (out of 100) based on solar ratio, recycled water ratio, and alert resolution
    solar_ratio = (total_solar / total_energy) if total_energy > 0 else 0.2
    water_recycle_ratio = (total_recycled_water / total_water) if total_water > 0 else 0.3
    score = int(min(100, max(50, (solar_ratio * 40) + (water_recycle_ratio * 40) + 38)))

    conn.close()
    return {
        "energy_consumption_kwh": total_energy,
        "solar_generation_kwh": total_solar,
        "water_consumption_l": total_water,
        "recycled_water_l": total_recycled_water,
        "waste_quantity_kg": total_waste,
        "waste_items_analyzed": waste_scans,
        "active_alerts": active_alerts,
        "carbon_savings_kg": carbon_saved_kg,
        "sustainability_score": score,
        "is_demo_data": True
    }


def get_energy_analytics():
    """Returns daily trend and per-building energy statistics."""
    conn = get_db_connection()
    c = conn.cursor()

    # Daily aggregation
    c.execute("""
        SELECT date(recorded_at) as day, 
               SUM(energy_used) as total_used, 
               SUM(solar_energy) as total_solar 
        FROM energy_consumption 
        GROUP BY date(recorded_at) 
        ORDER BY day ASC 
        LIMIT 7
    """)
    daily_rows = c.fetchall()

    # Facility breakdown
    c.execute("""
        SELECT building_name, 
               SUM(energy_used) as total_used, 
               SUM(solar_energy) as total_solar 
        FROM energy_consumption 
        GROUP BY building_name 
        ORDER BY total_used DESC
    """)
    facility_rows = c.fetchall()

    conn.close()

    days = [r["day"] for r in daily_rows]
    grid_data = [round(r["total_used"], 1) for r in daily_rows]
    solar_data = [round(r["total_solar"], 1) for r in daily_rows]

    facilities = [r["building_name"] for r in facility_rows]
    fac_used = [round(r["total_used"], 1) for r in facility_rows]
    fac_solar = [round(r["total_solar"], 1) for r in facility_rows]

    return {
        "daily": {"labels": days, "grid": grid_data, "solar": solar_data},
        "facilities": {"labels": facilities, "used": fac_used, "solar": fac_solar},
        "is_demo_data": True
    }


def get_water_analytics():
    """Returns water consumption trends and facility breakdowns."""
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        SELECT date(recorded_at) as day, 
               SUM(water_used) as total_used, 
               SUM(water_recycled) as total_recycled 
        FROM water_consumption 
        GROUP BY date(recorded_at) 
        ORDER BY day ASC 
        LIMIT 7
    """)
    daily_rows = c.fetchall()

    c.execute("""
        SELECT building_name, 
               SUM(water_used) as total_used, 
               SUM(water_recycled) as total_recycled 
        FROM water_consumption 
        GROUP BY building_name 
        ORDER BY total_used DESC
    """)
    facility_rows = c.fetchall()

    conn.close()

    days = [r["day"] for r in daily_rows]
    used_data = [round(r["total_used"], 1) for r in daily_rows]
    recycled_data = [round(r["total_recycled"], 1) for r in daily_rows]

    facilities = [r["building_name"] for r in facility_rows]
    fac_used = [round(r["total_used"], 1) for r in facility_rows]
    fac_recycled = [round(r["total_recycled"], 1) for r in facility_rows]

    return {
        "daily": {"labels": days, "consumed": used_data, "recycled": recycled_data},
        "facilities": {"labels": facilities, "consumed": fac_used, "recycled": fac_recycled},
        "is_demo_data": True
    }


def get_waste_analytics():
    """Returns waste categories, proportions, and disposal methods."""
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT waste_type, quantity_kg, disposal_method, recorded_at FROM waste_management ORDER BY quantity_kg DESC")
    rows = c.fetchall()

    c.execute("SELECT * FROM waste_detections ORDER BY timestamp DESC LIMIT 10")
    recent_detections = [dict(r) for r in c.fetchall()]

    conn.close()

    types = [r["waste_type"] for r in rows]
    quantities = [float(r["quantity_kg"]) for r in rows]
    methods = [r["disposal_method"] for r in rows]

    return {
        "types": types,
        "quantities": quantities,
        "methods": methods,
        "recent_detections": recent_detections,
        "is_demo_data": True
    }


def get_all_alerts(category=None, severity=None, status=None):
    """Returns alerts filtered by category, severity, or status."""
    conn = get_db_connection()
    c = conn.cursor()

    query = "SELECT * FROM alerts WHERE 1=1"
    params = []

    if category and category.lower() != 'all':
        query += " AND LOWER(category) = LOWER(?)"
        params.append(category)
    if severity and severity.lower() != 'all':
        query += " AND LOWER(severity) = LOWER(?)"
        params.append(severity)
    if status and status.lower() != 'all':
        query += " AND LOWER(status) = LOWER(?)"
        params.append(status)

    query += " ORDER BY CASE severity WHEN 'Critical' THEN 1 WHEN 'Warning' THEN 2 ELSE 3 END, timestamp DESC"

    c.execute(query, params)
    alerts = [dict(r) for r in c.fetchall()]
    conn.close()
    return alerts


def update_alert(alert_id, new_status):
    """Updates an alert status to 'Acknowledged' or 'Resolved'."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE alerts SET status = ? WHERE alert_id = ?", (new_status, alert_id))
    conn.commit()
    conn.close()
    return True


def get_all_recommendations():
    """Fetches recommendations from the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sustainability_recommendations ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def add_recommendation_record(category, recommendation, priority='Medium'):
    """Adds a new AI-generated or custom recommendation."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO sustainability_recommendations (category, recommendation, priority, status) VALUES (?, ?, ?, 'Pending')",
        (category, recommendation, priority)
    )
    rec_id = c.lastrowid
    conn.commit()
    conn.close()
    return rec_id


def save_waste_detection(image_name, detected_objects, confidence_score, classified_category, recyclable_status, carbon_offset_kg, model_used):
    """Saves a waste scan event into SQLite."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO waste_detections 
        (image_name, detected_objects, confidence_score, classified_category, recyclable_status, carbon_offset_kg, model_used)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (image_name, detected_objects, confidence_score, classified_category, recyclable_status, carbon_offset_kg, model_used))
    det_id = c.lastrowid
    conn.commit()
    conn.close()
    return det_id