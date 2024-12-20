-- Migration Script - Level 1 (Base Types and References)
-- Generated: 2024-12-19
-- Description: Creates base tables with no dependencies

BEGIN;

-- Enable error logging
CREATE TABLE IF NOT EXISTS migration_log (
    id SERIAL PRIMARY KEY,
    migration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    table_name VARCHAR(100),
    status VARCHAR(20),
    error_message TEXT,
    records_migrated INTEGER
);

-- Level 1.1: Type Tables (No Dependencies)
CREATE TABLE IF NOT EXISTS company_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS doctor_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Level 1.2: Reference Tables (No Dependencies)
CREATE TABLE IF NOT EXISTS icd10_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_icd10_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS icd9_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_icd9_code UNIQUE (code)
);

-- Add indexes and comments
CREATE INDEX idx_company_types_name ON company_types(name);
CREATE INDEX idx_customer_types_name ON customer_types(name);
CREATE INDEX idx_customer_classes_name ON customer_classes(name);
CREATE INDEX idx_doctor_types_name ON doctor_types(name);
CREATE INDEX idx_icd10_codes_code ON icd10_codes(code);
CREATE INDEX idx_icd9_codes_code ON icd9_codes(code);

COMMENT ON TABLE company_types IS 'Lookup table for company types';
COMMENT ON TABLE customer_types IS 'Lookup table for customer types';
COMMENT ON TABLE customer_classes IS 'Lookup table for customer classes';
COMMENT ON TABLE doctor_types IS 'Lookup table for doctor types';
COMMENT ON TABLE icd10_codes IS 'ICD-10 diagnosis codes reference table';
COMMENT ON TABLE icd9_codes IS 'ICD-9 diagnosis codes reference table';

COMMIT;
