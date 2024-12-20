-- Migration Script - Level 4.11 (Shipping and Delivery Management)
-- Generated: 2024-12-19
-- Description: Creates shipping, delivery, and order tracking tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS delivery_confirmations CASCADE;
DROP TABLE IF EXISTS delivery_routes CASCADE;
DROP TABLE IF EXISTS delivery_stops CASCADE;
DROP TABLE IF EXISTS shipping_packages CASCADE;
DROP TABLE IF EXISTS shipping_methods CASCADE;
DROP TABLE IF EXISTS shipping_carriers CASCADE;
DROP TABLE IF EXISTS shipping_zones CASCADE;

-- Level 4.29: Shipping Configuration
CREATE TABLE IF NOT EXISTS shipping_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    zip_codes TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_shipping_zone_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS shipping_carriers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50),
    api_key VARCHAR(100),
    api_secret VARCHAR(100),
    settings JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_shipping_carrier_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS shipping_methods (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    service_code VARCHAR(50),
    estimated_days INTEGER,
    handling_time INTEGER, -- in minutes
    cutoff_time TIME,
    is_signature_required BOOLEAN DEFAULT false,
    is_insurance_required BOOLEAN DEFAULT false,
    settings JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_shipping_method_carrier FOREIGN KEY (carrier_id) REFERENCES shipping_carriers(id),
    CONSTRAINT uq_shipping_method_carrier UNIQUE (carrier_id, service_code),
    CONSTRAINT chk_shipping_method_days CHECK (estimated_days > 0),
    CONSTRAINT chk_shipping_method_handling CHECK (handling_time >= 0)
);

-- Level 4.30: Package Management
CREATE TABLE IF NOT EXISTS shipping_packages (
    id SERIAL PRIMARY KEY,
    tracking_number VARCHAR(100),
    order_id INTEGER,
    shipping_method_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    ship_date DATE,
    estimated_delivery_date DATE,
    actual_delivery_date DATE,
    weight DECIMAL(10,2),
    length DECIMAL(10,2),
    width DECIMAL(10,2),
    height DECIMAL(10,2),
    declared_value DECIMAL(10,2),
    insurance_amount DECIMAL(10,2),
    shipping_cost DECIMAL(10,2),
    label_url VARCHAR(500),
    tracking_url VARCHAR(500),
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_shipping_package_method FOREIGN KEY (shipping_method_id) REFERENCES shipping_methods(id),
    CONSTRAINT chk_shipping_package_dates CHECK (
        ship_date <= estimated_delivery_date AND
        (actual_delivery_date IS NULL OR ship_date <= actual_delivery_date)
    ),
    CONSTRAINT chk_shipping_package_dimensions CHECK (
        weight > 0 AND length > 0 AND width > 0 AND height > 0
    ),
    CONSTRAINT chk_shipping_package_amounts CHECK (
        declared_value >= 0 AND
        insurance_amount >= 0 AND
        shipping_cost >= 0
    )
);

-- Level 4.31: Delivery Management
CREATE TABLE IF NOT EXISTS delivery_routes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    driver_id INTEGER,
    vehicle_id INTEGER,
    route_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    status VARCHAR(20) DEFAULT 'planned',
    total_stops INTEGER,
    total_distance DECIMAL(10,2),
    total_duration INTEGER, -- in minutes
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_delivery_route_driver FOREIGN KEY (driver_id) REFERENCES users(id),
    CONSTRAINT chk_delivery_route_times CHECK (
        start_time < end_time OR end_time IS NULL
    ),
    CONSTRAINT chk_delivery_route_metrics CHECK (
        (total_stops >= 0 OR total_stops IS NULL) AND
        (total_distance >= 0 OR total_distance IS NULL) AND
        (total_duration >= 0 OR total_duration IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS delivery_stops (
    id SERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    stop_number INTEGER NOT NULL,
    planned_arrival_time TIMESTAMP,
    actual_arrival_time TIMESTAMP,
    planned_departure_time TIMESTAMP,
    actual_departure_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    signature_required BOOLEAN DEFAULT false,
    signature_image TEXT,
    photo_proof TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_delivery_stop_route FOREIGN KEY (route_id) REFERENCES delivery_routes(id),
    CONSTRAINT fk_delivery_stop_package FOREIGN KEY (package_id) REFERENCES shipping_packages(id),
    CONSTRAINT chk_delivery_stop_times CHECK (
        planned_arrival_time < planned_departure_time AND
        (actual_arrival_time IS NULL OR actual_departure_time IS NULL OR
         actual_arrival_time < actual_departure_time)
    )
);

CREATE TABLE IF NOT EXISTS delivery_confirmations (
    id SERIAL PRIMARY KEY,
    stop_id INTEGER NOT NULL,
    confirmation_type VARCHAR(50) NOT NULL,
    confirmed_by VARCHAR(100),
    confirmation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    CONSTRAINT fk_delivery_confirmation_stop FOREIGN KEY (stop_id) REFERENCES delivery_stops(id)
);

-- Add indexes for better performance
CREATE INDEX idx_shipping_zones_active ON shipping_zones(is_active);
CREATE INDEX idx_shipping_carriers_active ON shipping_carriers(is_active);

CREATE INDEX idx_shipping_methods_carrier ON shipping_methods(carrier_id);
CREATE INDEX idx_shipping_methods_active ON shipping_methods(is_active);

CREATE INDEX idx_shipping_packages_tracking ON shipping_packages(tracking_number);
CREATE INDEX idx_shipping_packages_order ON shipping_packages(order_id);
CREATE INDEX idx_shipping_packages_method ON shipping_packages(shipping_method_id);
CREATE INDEX idx_shipping_packages_dates ON shipping_packages(ship_date, estimated_delivery_date, actual_delivery_date);
CREATE INDEX idx_shipping_packages_status ON shipping_packages(status);

CREATE INDEX idx_delivery_routes_driver ON delivery_routes(driver_id);
CREATE INDEX idx_delivery_routes_date ON delivery_routes(route_date);
CREATE INDEX idx_delivery_routes_status ON delivery_routes(status);

CREATE INDEX idx_delivery_stops_route ON delivery_stops(route_id);
CREATE INDEX idx_delivery_stops_package ON delivery_stops(package_id);
CREATE INDEX idx_delivery_stops_times ON delivery_stops(planned_arrival_time, actual_arrival_time);
CREATE INDEX idx_delivery_stops_status ON delivery_stops(status);

CREATE INDEX idx_delivery_confirmations_stop ON delivery_confirmations(stop_id);
CREATE INDEX idx_delivery_confirmations_type ON delivery_confirmations(confirmation_type);

-- Add comments for documentation
COMMENT ON TABLE shipping_zones IS 'Geographic shipping zones';
COMMENT ON TABLE shipping_carriers IS 'Shipping carrier configurations';
COMMENT ON TABLE shipping_methods IS 'Available shipping methods per carrier';
COMMENT ON TABLE shipping_packages IS 'Package tracking and delivery status';
COMMENT ON TABLE delivery_routes IS 'Delivery route planning';
COMMENT ON TABLE delivery_stops IS 'Individual stops on delivery routes';
COMMENT ON TABLE delivery_confirmations IS 'Delivery confirmation records';

COMMIT;
