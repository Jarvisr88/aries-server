-- Migration Script - Level 2 (Tables with Level 1 Dependencies)
-- Generated: 2024-12-19
-- Description: Creates tables that depend on Level 1 tables

BEGIN;

-- Level 2.1: Medical Reference Tables
CREATE TABLE IF NOT EXISTS medical_conditions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icd10_code_id INTEGER REFERENCES icd10_codes(id),
    icd9_code_id INTEGER REFERENCES icd9_codes(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Level 2.2: System Configuration Tables
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    description TEXT,
    setting_type VARCHAR(50),
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_setting_key UNIQUE (setting_key)
);

CREATE TABLE IF NOT EXISTS variables (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    value TEXT,
    description TEXT,
    variable_type VARCHAR(50),
    is_system BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_variable_name UNIQUE (name)
);

-- Add indexes
CREATE INDEX idx_medical_conditions_name ON medical_conditions(name);
CREATE INDEX idx_medical_conditions_icd10 ON medical_conditions(icd10_code_id);
CREATE INDEX idx_medical_conditions_icd9 ON medical_conditions(icd9_code_id);
CREATE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_variables_name ON variables(name);

-- Add comments
COMMENT ON TABLE medical_conditions IS 'Medical conditions with ICD code references';
COMMENT ON TABLE system_settings IS 'System-wide configuration settings';
COMMENT ON TABLE variables IS 'System and user-defined variables';

COMMIT;
