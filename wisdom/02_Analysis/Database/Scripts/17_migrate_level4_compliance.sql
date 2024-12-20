-- Migration Script - Level 4.1 (Compliance and Company Tables)
-- Generated: 2024-12-19
-- Description: Creates compliance and company-related tables

BEGIN;

-- Level 4.1: Compliance Tables
CREATE TABLE IF NOT EXISTS compliance (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    customer_id INTEGER,
    form_type VARCHAR(50),
    status VARCHAR(20),
    compliance_date DATE,
    expiry_date DATE,
    last_review_date DATE,
    next_review_date DATE,
    is_compliant BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_compliance_company FOREIGN KEY (company_id) REFERENCES companies(id),
    CONSTRAINT fk_compliance_customer FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS compliance_notes (
    id SERIAL PRIMARY KEY,
    compliance_id INTEGER NOT NULL,
    note_type VARCHAR(50),
    note_text TEXT,
    is_internal BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_compliance_note FOREIGN KEY (compliance_id) REFERENCES compliance(id)
);

-- Level 4.2: Location Tables
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    address_line1 VARCHAR(100),
    address_line2 VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    country VARCHAR(50) DEFAULT 'USA',
    phone VARCHAR(20),
    fax VARCHAR(20),
    email VARCHAR(100),
    is_primary BOOLEAN DEFAULT false,
    is_billing BOOLEAN DEFAULT false,
    is_shipping BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_location_company FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Level 4.3: Legal Representative Tables
CREATE TABLE IF NOT EXISTS legal_representatives (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    title VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    is_primary BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_legal_rep_company FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Add indexes for better performance
CREATE INDEX idx_compliance_company ON compliance(company_id);
CREATE INDEX idx_compliance_customer ON compliance(customer_id);
CREATE INDEX idx_compliance_dates ON compliance(compliance_date, expiry_date, next_review_date);
CREATE INDEX idx_compliance_status ON compliance(status);

CREATE INDEX idx_compliance_notes_compliance ON compliance_notes(compliance_id);
CREATE INDEX idx_compliance_notes_type ON compliance_notes(note_type);

CREATE INDEX idx_locations_company ON locations(company_id);
CREATE INDEX idx_locations_state_city ON locations(state, city);
CREATE INDEX idx_locations_zip ON locations(zip_code);

CREATE INDEX idx_legal_reps_company ON legal_representatives(company_id);
CREATE INDEX idx_legal_reps_name ON legal_representatives(last_name, first_name);
CREATE INDEX idx_legal_reps_dates ON legal_representatives(start_date, end_date);

-- Add comments for documentation
COMMENT ON TABLE compliance IS 'Tracks compliance status for companies and customers';
COMMENT ON TABLE compliance_notes IS 'Notes and documentation related to compliance records';
COMMENT ON TABLE locations IS 'Physical locations for companies';
COMMENT ON TABLE legal_representatives IS 'Legal representatives for companies';

-- Add constraints for data integrity
ALTER TABLE compliance 
    ADD CONSTRAINT chk_compliance_dates 
    CHECK (compliance_date <= expiry_date AND last_review_date <= next_review_date);

ALTER TABLE locations
    ADD CONSTRAINT chk_location_address
    CHECK (address_line1 IS NOT NULL OR (is_primary = false AND is_billing = false AND is_shipping = false));

ALTER TABLE legal_representatives
    ADD CONSTRAINT chk_legal_rep_dates
    CHECK (start_date <= end_date OR end_date IS NULL);

COMMIT;
