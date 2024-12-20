-- Migration Script - Level 4.23 (Base Tables)
-- Generated: 2024-12-19
-- Description: Creates foundational tables required by other scripts

DO $$ 
BEGIN

-- Drop existing tables if they exist
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS doctors CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS addresses CASCADE;

-- Create base tables in order of dependencies
CREATE TABLE IF NOT EXISTS addresses (
    id SERIAL PRIMARY KEY,
    address_type VARCHAR(50),
    address_line1 VARCHAR(200) NOT NULL,
    address_line2 VARCHAR(200),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(100) DEFAULT 'USA',
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    is_verified BOOLEAN DEFAULT false,
    is_primary BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    ssn VARCHAR(11),
    email VARCHAR(255),
    phone_primary VARCHAR(20),
    phone_secondary VARCHAR(20),
    address_id INTEGER,
    emergency_contact JSONB,
    insurance_info JSONB,
    medical_history JSONB,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_patient_address FOREIGN KEY (address_id) REFERENCES addresses(id)
);

CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    specialty VARCHAR(100),
    license_number VARCHAR(50) NOT NULL,
    npi_number VARCHAR(10),
    email VARCHAR(255),
    phone_primary VARCHAR(20),
    phone_secondary VARCHAR(20),
    fax VARCHAR(20),
    address_id INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_doctor_address FOREIGN KEY (address_id) REFERENCES addresses(id),
    CONSTRAINT uq_doctor_license UNIQUE (license_number),
    CONSTRAINT uq_doctor_npi UNIQUE (npi_number)
);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    employee_id VARCHAR(50) NOT NULL,
    department VARCHAR(100),
    position VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    hire_date DATE NOT NULL,
    termination_date DATE,
    address_id INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_employee_address FOREIGN KEY (address_id) REFERENCES addresses(id),
    CONSTRAINT uq_employee_id UNIQUE (employee_id)
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INTEGER,
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    unit_of_measure VARCHAR(50),
    dimensions JSONB,
    weight DECIMAL(10,2),
    specifications JSONB,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_product_sku UNIQUE (sku)
);

-- Add indexes for better performance
CREATE INDEX idx_addresses_postal ON addresses(postal_code);
CREATE INDEX idx_addresses_city_state ON addresses(city, state);

CREATE INDEX idx_patients_name ON patients(last_name, first_name);
CREATE INDEX idx_patients_dob ON patients(date_of_birth);
CREATE INDEX idx_patients_status ON patients(status);

CREATE INDEX idx_doctors_name ON doctors(last_name, first_name);
CREATE INDEX idx_doctors_license ON doctors(license_number);
CREATE INDEX idx_doctors_npi ON doctors(npi_number);
CREATE INDEX idx_doctors_status ON doctors(status);

CREATE INDEX idx_employees_name ON employees(last_name, first_name);
CREATE INDEX idx_employees_department ON employees(department);
CREATE INDEX idx_employees_status ON employees(status);

CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active);

-- Add comments for documentation
COMMENT ON TABLE addresses IS 'Physical and mailing addresses';
COMMENT ON TABLE patients IS 'Patient demographic and contact information';
COMMENT ON TABLE doctors IS 'Healthcare provider information';
COMMENT ON TABLE employees IS 'Employee records';
COMMENT ON TABLE products IS 'Product catalog information';

EXCEPTION WHEN OTHERS THEN
    -- Roll back the transaction on error
    RAISE NOTICE 'Error occurred: %', SQLERRM;
    RAISE EXCEPTION 'Transaction aborted';
END;
$$ LANGUAGE plpgsql;
