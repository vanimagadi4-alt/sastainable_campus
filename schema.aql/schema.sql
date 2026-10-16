-- EcoNova AI: Intelligent Digital Twin for Sustainable Campuses
-- Database Schema for Dayananda Sagar University (DSU), Harohalli Campus

-- Optional MySQL database initialization:
-- CREATE DATABASE IF NOT EXISTS ecotwin_ai;
-- USE ecotwin_ai;

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(30) DEFAULT 'Student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Energy Consumption
CREATE TABLE IF NOT EXISTS energy_consumption (
    energy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_name VARCHAR(100) NOT NULL,
    energy_used DECIMAL(10,2) NOT NULL,
    solar_energy DECIMAL(10,2) DEFAULT 0,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. Water Consumption
CREATE TABLE IF NOT EXISTS water_consumption (
    water_id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_name VARCHAR(100) NOT NULL,
    water_used DECIMAL(10,2) NOT NULL,
    water_recycled DECIMAL(10,2) DEFAULT 0,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. Waste Management
CREATE TABLE IF NOT EXISTS waste_management (
    waste_id INTEGER PRIMARY KEY AUTOINCREMENT,
    waste_type VARCHAR(50) NOT NULL,
    quantity_kg DECIMAL(10,2) NOT NULL,
    disposal_method VARCHAR(50),
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. Air Quality
CREATE TABLE IF NOT EXISTS air_quality (
    air_id INTEGER PRIMARY KEY AUTOINCREMENT,
    location VARCHAR(100) NOT NULL,
    co2_level DECIMAL(10,2),
    pm25_level DECIMAL(10,2),
    temperature DECIMAL(5,2),
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. Sustainability Recommendations
CREATE TABLE IF NOT EXISTS sustainability_recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    recommendation TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'Medium',
    status VARCHAR(30) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Carbon Emissions
CREATE TABLE IF NOT EXISTS carbon_emissions (
    emission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source VARCHAR(100) NOT NULL,
    activity_value DECIMAL(10,2) NOT NULL,
    emission_factor DECIMAL(10,4) NOT NULL,
    co2_equivalent_kg DECIMAL(12,2) NOT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 8. Sustainability Actions
CREATE TABLE IF NOT EXISTS sustainability_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INT,
    activity_name VARCHAR(100) NOT NULL,
    points INT DEFAULT 0,
    activity_date DATE,
    verification_status VARCHAR(30) DEFAULT 'Pending',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 9. Campus Alerts (Priority Action Center)
CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(150) NOT NULL,
    facility VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'Critical', 'Warning', 'Info'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'Active' -- 'Active', 'Acknowledged', 'Resolved'
);