-- ============================================================================
-- EcoCampus AI - Seed Data Script
-- Populates campus.db with verified facilities, technician directory,
-- initial maintenance alerts, AI waste audits, and telemetry readings.
-- ============================================================================

-- 1. Insert Facilities (Dayananda Sagar University Master Directory)
INSERT OR REPLACE INTO facilities (id, name, zone, floors, area_sqft, occupancy_capacity, baseline_energy_kwh, baseline_water_liters, description, brochure_source_pages, brochure_url)
VALUES 
('academic-research', 'Academic & Research Facilities', 'North Quad', 5, 85000, 1500, 312.0, 820.0, 'Laboratories, classrooms, and interdisciplinary research centers.', '8-9, 16', 'https://dsu.edu.in/images/E_brochure_08022024.pdf'),
('library', 'Central Library & Scholarly Hub', 'East Quad', 3, 42000, 650, 210.0, 750.0, 'Digital scholarly resources, study spaces, and learning resources.', '16', 'https://dsu.edu.in/images/E_brochure_08022024.pdf'),
('innovation-maker', 'Innovation Labs & Maker Spaces', 'West Quad', 4, 38000, 500, 240.0, 410.0, 'Prototyping facilities, collaborative robotics studios, and maker zones.', '8-9', 'https://dsu.edu.in/images/E_brochure_08022024.pdf'),
('sports-fitness', 'Sports & Fitness Pavilion', 'North Grounds', 2, 65000, 1200, 145.0, 480.0, 'Indoor gymnasium, courts, cultural arena, and athlete facilities.', '20-21', 'https://dsu.edu.in/images/E_brochure_08022024.pdf'),
('medical-campus', 'CDSIMER Hospital & Medical College', 'South Campus', 6, 140000, 2200, 680.0, 2400.0, 'Chandramma Dayananda Sagar Institute of Medical Education & Research teaching hospital.', '20-21', 'https://dsu.edu.in/images/E_brochure_08022024.pdf'),
('solar-infrastructure', 'Solar Canopy & Microgrid', 'South Campus Roofs', 1, 32000, 0, -420.0, 60.0, 'Rooftop photovoltaic arrays generating clean renewable microgrid power.', '2-3', 'https://dsu.edu.in/images/E_brochure_08022024.pdf');

-- 2. Insert Technicians Directory
INSERT OR REPLACE INTO technicians (id, name, role, team, email, phone, specialization, status, active_work_orders)
VALUES
(1, 'Marcus Vance', 'Senior HVAC Specialist', 'Facility Crew Alpha', 'm.vance@campus.edu', '+91 98765 43210', 'Energy/HVAC', 'Active', 1),
(2, 'Priya Sharma', 'Lead Plumbing Engineer', 'Plumbing Rapid Unit 2', 'p.sharma@campus.edu', '+91 98765 43211', 'Plumbing/Piping', 'Active', 1),
(3, 'Rajesh Kumar', 'Custodial Operations Lead', 'Custodial Team Alpha', 'r.kumar@campus.edu', '+91 98765 43212', 'Waste Logistics', 'Active', 1),
(4, 'Ananya Patel', 'Student Sustainability Lead', 'Student Eco Volunteer Guild', 'a.patel@campus.edu', '+91 98765 43213', 'Waste Logistics', 'Active', 0),
(5, 'Vikram Singh', 'Solar Electrical Tech', 'Green Energy Patrol', 'v.singh@campus.edu', '+91 98765 43214', 'Solar PV', 'On Call', 0);

-- 3. Insert Initial Corrective Action Alerts
INSERT OR REPLACE INTO alerts (id, title, category, location, priority, evidence, action, status, created_at, source, impact_estimate, facility_id, assignee, notes, sla_hours, cost_savings, co2_savings, energy_savings_kwh, water_savings_liters, waste_diverted_kg)
VALUES
(1, 'High Volume Recyclable Accumulation', 'Waste', 'Student Canteen Patio', 'High', 'AI computer vision identified 4 plastic bottles & 2 cups near south patio bin.', 'Dispatch custodial team for immediate sorting & bin clearance.', 'Open', '2026-10-15 11:30', 'AI Detection', 'Diverts ~6.5 kg recyclable materials from landfill', 'academic-research', 'Custodial Team Alpha', 'Auxiliary 240L dual-stream sorting bin dispatched.', 4, 18.5, 14.2, 0.0, 0.0, 6.5),
(2, 'Excessive After-Hours Energy Consumption', 'Energy', 'Block C Auditorium', 'Medium', 'Continuous 38 kWh load detected between 12:00 AM - 4:00 AM (+34% above baseline).', 'Inspect auditorium central HVAC timer and laboratory lighting overrides.', 'In Progress', '2026-10-15 08:15', 'Sensor Rule', 'Saves ~45 kWh/night (~18 kg CO2e reduction)', 'academic-research', 'Facility Crew Alpha', 'Auditorium BMS timer reset scheduled for 18:00.', 12, 42.0, 36.9, 45.0, 0.0, 0.0),
(3, 'Unusual Nighttime Water Flow Detected', 'Water', 'Central Library 2nd Floor', 'High', 'Continuous baseline flow of 165 L/hr detected during 2:00 AM - 5:00 AM closure window.', 'Check 2nd-floor washroom flushometers and main riser valves for continuous leakage.', 'Open', '2026-10-15 06:45', 'Sensor Rule', 'Conserves ~490 L/day of treated water', 'library', 'Plumbing Rapid Unit 2', '2nd-floor isolation valve inspected; replacing diaphragm seal.', 4, 24.5, 8.4, 0.0, 490.0, 0.0),
(4, 'Solar Array Inverter Efficiency Derating', 'Energy', 'Solar Canopy Arrays', 'Low', 'Inverter efficiency dropped 11% due to dust accumulation on western array strings.', 'Schedule bi-weekly panel washdown during cool early morning hours.', 'Completed', '2026-10-14 06:30', 'Sensor Rule', 'Recovers ~22 kWh/day clean power generation', 'solar-infrastructure', 'Green Energy Patrol', 'Panel wash completed; inverter output restored to 94% peak.', 24, 38.0, 31.2, 22.0, 0.0, 0.0),
(5, 'Littering Hotspot near Botanical Garden Walkway', 'Waste', 'Eco Park Garden Walkway', 'Medium', 'AI detected discarded beverage containers and snack wrappers along south footpath.', 'Install additional dual-stream recycling receptacle and schedule student volunteer sweep.', 'Completed', '2026-10-13 14:00', 'Manual Inspection', 'Protects local pollinator garden soil & cleanliness', 'sports-fitness', 'Student Eco Volunteer Guild', 'Twin receptacles anchored and student sweep completed.', 12, 12.0, 9.5, 0.0, 0.0, 8.0);

-- 4. Insert Sample AI Waste Vision Audit Logs
INSERT OR REPLACE INTO waste_audit_logs (id, image_filename, annotated_image_path, total_objects, waste_objects, recyclable_count, organic_count, packaging_count, model_version, inference_time_ms, human_verified, linked_alert_id, created_at)
VALUES
(1, 'canteen_bottles.jpg', '/static/latest_detection.jpg', 6, 6, 4, 2, 0, 'YOLOv8n', 298.5, 1, 1, '2026-10-15 11:28'),
(2, 'cafeteria_tray.jpg', '/static/detections/detection_17290001.jpg', 4, 3, 1, 2, 1, 'YOLOv8n', 312.0, 1, NULL, '2026-10-15 10:15'),
(3, 'sample_campus_bus.jpg', '/static/detections/detection_17290002.jpg', 6, 0, 0, 0, 0, 'YOLOv8n', 305.2, 1, NULL, '2026-10-14 16:40');

-- 5. Insert Sample CSV Ingestion Import Log
INSERT OR REPLACE INTO meter_imports (id, filename, imported_at, reading_count, mean_value, peak_value, anomalies_flagged)
VALUES
(1, 'sample_meter_data.csv', '2026-10-15 16:00:00', 24, 88.5, 170.5, 3);

-- 6. Insert Historical ESG Monthly Audits
INSERT OR REPLACE INTO esg_monthly_audits (id, audit_month, total_tickets_logged, tickets_resolved, resolution_rate_pct, electricity_saved_kwh, water_conserved_liters, waste_diverted_kg, ghg_co2e_avoided_kg, cost_avoidance_usd, cost_avoidance_inr, compliance_score, audited_at)
VALUES
(1, '2026-09', 28, 26, 92.8, 4200.0, 36000.0, 480.0, 3444.0, 732.0, 60756.0, 91, '2026-10-01 00:00'),
(2, '2026-10', 14, 9, 64.3, 1840.0, 12400.0, 245.0, 1508.8, 307.2, 25497.6, 86, '2026-10-15 20:00');
