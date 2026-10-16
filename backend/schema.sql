-- ============================================================================
-- EcoCampus AI - Relational Database Schema (SQLite 3)
-- Database Name: campus.db
-- Purpose: Unified campus sustainability operations, computer vision audits,
--          energy/water telemetry, work orders, and ESG compliance tracking.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. FACILITIES (Campus Facility Master & Digital Twin Metadata)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS facilities (
    id TEXT PRIMARY KEY,                       -- e.g. 'academic-research', 'library', 'solar-infrastructure'
    name TEXT NOT NULL,                        -- Official facility name
    zone TEXT NOT NULL,                        -- Campus quad/zone (e.g. 'North Quad', 'South Campus')
    floors INTEGER DEFAULT 3,                  -- Number of floors
    area_sqft INTEGER DEFAULT 45000,           -- Total built-up area in square feet
    occupancy_capacity INTEGER DEFAULT 800,    -- Rated occupancy capacity
    baseline_energy_kwh REAL DEFAULT 290.0,    -- Target daily electricity benchmark (kWh)
    baseline_water_liters REAL DEFAULT 800.0,  -- Target daily water benchmark (Liters)
    description TEXT,                          -- Functional description
    brochure_source_pages TEXT,                -- E-brochure reference page numbers
    brochure_url TEXT,                         -- URL link to verifiable institutional reference
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 2. TECHNICIANS (Facility Staff, Rapid Response & Volunteer Guilds)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS technicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                        -- e.g. 'Marcus Vance', 'Priya Sharma'
    role TEXT NOT NULL,                        -- e.g. 'Lead Electrician', 'Plumbing Specialist', 'Custodial Lead'
    team TEXT NOT NULL,                        -- e.g. 'Facility Crew Alpha', 'Plumbing Unit 2', 'Green Volunteers Guild'
    email TEXT,                                -- Contact email
    phone TEXT,                                -- Contact phone
    specialization TEXT,                       -- 'Energy/HVAC', 'Plumbing/Piping', 'Waste Logistics', 'Solar PV'
    status TEXT DEFAULT 'Active',              -- 'Active', 'On Call', 'Off Duty'
    active_work_orders INTEGER DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- 3. ALERTS / WORK ORDERS (Corrective Action Dispatch & SLA Tracking)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                       -- Descriptive issue summary
    category TEXT NOT NULL,                    -- 'Waste', 'Energy', 'Water'
    location TEXT NOT NULL,                    -- Physical location (e.g. 'Student Canteen Patio')
    priority TEXT NOT NULL,                    -- 'High', 'Medium', 'Low'
    evidence TEXT NOT NULL,                    -- Telemetry delta or YOLO detection evidence
    action TEXT NOT NULL,                      -- Corrective action plan
    status TEXT NOT NULL DEFAULT 'Open',       -- 'Open', 'In Progress', 'Completed'
    created_at TEXT NOT NULL,                  -- ISO timestamp (YYYY-MM-DD HH:MM)
    source TEXT NOT NULL DEFAULT 'Manual',     -- 'AI Detection', 'Sensor Rule', 'Manual Inspection'
    impact_estimate TEXT,                      -- Human-readable impact summary
    facility_id TEXT REFERENCES facilities(id) ON DELETE SET NULL,
    assignee TEXT DEFAULT 'Facility Crew Alpha',-- Assigned technician or crew
    notes TEXT DEFAULT '',                     -- Technician resolution notes
    sla_hours INTEGER DEFAULT 4,               -- Target resolution turnaround time in hours
    cost_savings REAL DEFAULT 0.0,             -- Verified or modeled cost avoidance ($ or ₹)
    co2_savings REAL DEFAULT 0.0,              -- Verified or modeled CO2e avoided (kg)
    energy_savings_kwh REAL DEFAULT 0.0,       -- Electricity avoided (kWh)
    water_savings_liters REAL DEFAULT 0.0,     -- Water conserved (Liters)
    waste_diverted_kg REAL DEFAULT 0.0         -- Landfill waste diverted (kg)
);

-- ----------------------------------------------------------------------------
-- 4. WASTE AUDIT LOGS (AI Computer Vision Inference Archive)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS waste_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_filename TEXT NOT NULL,              -- Saved image reference (e.g. 'detection_17290000.jpg')
    annotated_image_path TEXT NOT NULL,        -- Relative path to bounding-box visualization
    total_objects INTEGER NOT NULL DEFAULT 0,  -- Total COCO objects detected
    waste_objects INTEGER NOT NULL DEFAULT 0,  -- Objects mapped to waste categories
    recyclable_count INTEGER DEFAULT 0,        -- Bottles, cans, cups, cutlery
    organic_count INTEGER DEFAULT 0,           -- Fruit peels, food scraps
    packaging_count INTEGER DEFAULT 0,         -- Takeout containers, boxes, bags
    model_version TEXT DEFAULT 'YOLOv8n',      -- Inference model identifier
    inference_time_ms REAL,                    -- Model inference latency in milliseconds
    human_verified INTEGER DEFAULT 0,          -- 0 = Pending verification, 1 = Verified by staff
    linked_alert_id INTEGER REFERENCES alerts(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- 5. METER IMPORTS (Utility Spreadsheet Ingestion Log)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meter_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,                    -- Uploaded CSV filename
    imported_at TEXT NOT NULL,                 -- Timestamp of ingestion
    reading_count INTEGER NOT NULL,            -- Total data points ingested
    mean_value REAL,                           -- Average consumption value
    peak_value REAL,                           -- Maximum observed spike
    anomalies_flagged INTEGER DEFAULT 0        -- Points exceeding baseline threshold
);

-- ----------------------------------------------------------------------------
-- 6. METER READINGS (Time-Series Resource Telemetry)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meter_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id INTEGER REFERENCES meter_imports(id) ON DELETE CASCADE,
    facility_id TEXT REFERENCES facilities(id) ON DELETE SET NULL,
    facility_label TEXT,                       -- Display name of building/meter
    metric TEXT NOT NULL,                      -- 'energy_kwh', 'water_liters', 'solar_kw', 'power_factor'
    value REAL NOT NULL,                       -- Numeric sensor reading
    unit TEXT NOT NULL,                        -- 'kWh', 'Liters', 'kW', 'L/min'
    measured_at TEXT NOT NULL,                 -- Sensor reading timestamp
    is_anomaly INTEGER NOT NULL DEFAULT 0,     -- 1 if flagged by threshold heuristic
    anomaly_rule TEXT                          -- e.g. 'EN-04_OVERNIGHT_SURGE'
);

-- ----------------------------------------------------------------------------
-- 7. ESG MONTHLY AUDITS (Institutional Sustainability Reporting History)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS esg_monthly_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_month TEXT NOT NULL UNIQUE,          -- Format 'YYYY-MM' (e.g. '2026-10')
    total_tickets_logged INTEGER DEFAULT 0,
    tickets_resolved INTEGER DEFAULT 0,
    resolution_rate_pct REAL DEFAULT 0.0,
    electricity_saved_kwh REAL DEFAULT 0.0,
    water_conserved_liters REAL DEFAULT 0.0,
    waste_diverted_kg REAL DEFAULT 0.0,
    ghg_co2e_avoided_kg REAL DEFAULT 0.0,
    cost_avoidance_usd REAL DEFAULT 0.0,
    cost_avoidance_inr REAL DEFAULT 0.0,
    compliance_score INTEGER DEFAULT 86,
    audited_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------------------------
-- INDEXES FOR PERFORMANCE
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_alerts_facility ON alerts(facility_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_category ON alerts(category);
CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority);
CREATE INDEX IF NOT EXISTS idx_meter_readings_time ON meter_readings(measured_at);
CREATE INDEX IF NOT EXISTS idx_meter_readings_facility ON meter_readings(facility_id);
CREATE INDEX IF NOT EXISTS idx_waste_audit_time ON waste_audit_logs(created_at);
