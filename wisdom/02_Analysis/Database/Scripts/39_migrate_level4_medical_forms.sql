-- Migration Script - Level 4.23 (Medical Forms and Healthcare Tables)
-- Generated: 2024-12-19
-- Description: Creates tables for CMN forms, medical codes, and healthcare data

DO $$ 
BEGIN

-- Drop existing tables if they exist
DROP TABLE IF EXISTS cmn_form_responses CASCADE;
DROP TABLE IF EXISTS cmn_form_fields CASCADE;
DROP TABLE IF EXISTS cmn_form_sections CASCADE;
DROP TABLE IF EXISTS cmn_forms CASCADE;
DROP TABLE IF EXISTS icd_codes CASCADE;
DROP TABLE IF EXISTS medical_conditions CASCADE;

-- First create the ICD codes table as it has no dependencies
CREATE TABLE IF NOT EXISTS icd_codes (
    id SERIAL PRIMARY KEY,
    code_type VARCHAR(10) NOT NULL,
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    is_billable BOOLEAN DEFAULT true,
    effective_date DATE,
    end_date DATE,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_icd_code UNIQUE (code_type, code),
    CONSTRAINT chk_code_type CHECK (code_type IN ('ICD-9', 'ICD-10')),
    CONSTRAINT chk_icd_dates CHECK (
        effective_date <= end_date OR end_date IS NULL
    )
);

-- Then create medical conditions
CREATE TABLE IF NOT EXISTS medical_conditions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icd_codes JSONB,
    category VARCHAR(100),
    severity VARCHAR(20),
    chronic BOOLEAN DEFAULT false,
    symptoms TEXT[],
    treatments TEXT[],
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_medical_condition_name UNIQUE (name),
    CONSTRAINT chk_condition_severity CHECK (
        severity IN ('mild', 'moderate', 'severe', 'critical')
    )
);

-- Create CMN form tables
CREATE TABLE IF NOT EXISTS cmn_forms (
    id SERIAL PRIMARY KEY,
    form_type VARCHAR(10) NOT NULL,
    form_version VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_cmn_form UNIQUE (form_type, form_version)
);

CREATE TABLE IF NOT EXISTS cmn_form_sections (
    id SERIAL PRIMARY KEY,
    form_id INTEGER NOT NULL,
    section_type CHAR(1) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL,
    is_required BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cmn_section_form FOREIGN KEY (form_id) REFERENCES cmn_forms(id),
    CONSTRAINT chk_section_type CHECK (section_type IN ('A', 'B', 'C')),
    CONSTRAINT uq_cmn_section UNIQUE (form_id, section_type)
);

CREATE TABLE IF NOT EXISTS cmn_form_fields (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    label TEXT NOT NULL,
    description TEXT,
    default_value TEXT,
    validation_rules JSONB,
    display_order INTEGER NOT NULL,
    is_required BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cmn_field_section FOREIGN KEY (section_id) REFERENCES cmn_form_sections(id),
    CONSTRAINT uq_cmn_field UNIQUE (section_id, field_name),
    CONSTRAINT chk_field_type CHECK (
        field_type IN ('text', 'number', 'date', 'boolean', 'select', 'multi-select', 'radio', 'checkbox')
    )
);

CREATE TABLE IF NOT EXISTS cmn_form_responses (
    id SERIAL PRIMARY KEY,
    form_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER,
    status VARCHAR(20) DEFAULT 'draft',
    responses JSONB NOT NULL,
    submitted_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(50),
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_cmn_response_form FOREIGN KEY (form_id) REFERENCES cmn_forms(id),
    CONSTRAINT fk_cmn_response_patient FOREIGN KEY (patient_id) REFERENCES patients(id),
    CONSTRAINT fk_cmn_response_doctor FOREIGN KEY (doctor_id) REFERENCES doctors(id),
    CONSTRAINT chk_response_status CHECK (
        status IN ('draft', 'submitted', 'reviewed', 'approved', 'rejected')
    )
);

-- Add indexes for better performance
CREATE INDEX idx_icd_codes_type ON icd_codes(code_type);
CREATE INDEX idx_icd_codes_code ON icd_codes(code);
CREATE INDEX idx_icd_codes_category ON icd_codes(category, sub_category);
CREATE INDEX idx_icd_codes_billable ON icd_codes(is_billable);
CREATE INDEX idx_icd_codes_dates ON icd_codes(effective_date, end_date);

CREATE INDEX idx_medical_conditions_category ON medical_conditions(category);
CREATE INDEX idx_medical_conditions_severity ON medical_conditions(severity);
CREATE INDEX idx_medical_conditions_chronic ON medical_conditions(chronic);

CREATE INDEX idx_cmn_forms_type ON cmn_forms(form_type, form_version);
CREATE INDEX idx_cmn_forms_active ON cmn_forms(is_active);

CREATE INDEX idx_cmn_sections_form ON cmn_form_sections(form_id);
CREATE INDEX idx_cmn_sections_type ON cmn_form_sections(section_type);
CREATE INDEX idx_cmn_sections_order ON cmn_form_sections(display_order);

CREATE INDEX idx_cmn_fields_section ON cmn_form_fields(section_id);
CREATE INDEX idx_cmn_fields_type ON cmn_form_fields(field_type);
CREATE INDEX idx_cmn_fields_order ON cmn_form_fields(display_order);
CREATE INDEX idx_cmn_fields_active ON cmn_form_fields(is_active);

CREATE INDEX idx_cmn_responses_form ON cmn_form_responses(form_id);
CREATE INDEX idx_cmn_responses_patient ON cmn_form_responses(patient_id);
CREATE INDEX idx_cmn_responses_doctor ON cmn_form_responses(doctor_id);
CREATE INDEX idx_cmn_responses_status ON cmn_form_responses(status);
CREATE INDEX idx_cmn_responses_dates ON cmn_form_responses(submitted_at, reviewed_at);

-- Add comments for documentation
COMMENT ON TABLE icd_codes IS 'ICD-9 and ICD-10 diagnosis codes';
COMMENT ON TABLE medical_conditions IS 'Medical condition definitions and metadata';
COMMENT ON TABLE cmn_forms IS 'Certificate of Medical Necessity form definitions';
COMMENT ON TABLE cmn_form_sections IS 'Sections within CMN forms';
COMMENT ON TABLE cmn_form_fields IS 'Field definitions for CMN form sections';
COMMENT ON TABLE cmn_form_responses IS 'Completed CMN form responses';

EXCEPTION WHEN OTHERS THEN
    -- Roll back the transaction on error
    RAISE NOTICE 'Error occurred: %', SQLERRM;
    RAISE EXCEPTION 'Transaction aborted';
END;
$$ LANGUAGE plpgsql;
