-- Migration Script - Level 4.6 (Eligibility and Denial Management)
-- Generated: 2024-12-19
-- Description: Creates eligibility request and denial tracking tables

BEGIN;

-- Level 4.17: Base Tables (if not exist)
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_number VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS insurance_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

-- Level 4.17: Eligibility Management
CREATE TABLE IF NOT EXISTS eligibility_requests (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    insurance_id INTEGER NOT NULL,
    request_date TIMESTAMP NOT NULL,
    service_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    response_date TIMESTAMP,
    is_eligible BOOLEAN,
    coverage_start_date DATE,
    coverage_end_date DATE,
    benefit_details JSONB,
    response_data JSONB,
    error_message TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_eligibility_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_eligibility_insurance FOREIGN KEY (insurance_id) REFERENCES insurance_types(id),
    CONSTRAINT chk_eligibility_dates CHECK (
        request_date <= response_date OR response_date IS NULL
    )
);

-- Level 4.18: Denial Management
CREATE TABLE IF NOT EXISTS denials (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    insurance_id INTEGER NOT NULL,
    claim_number VARCHAR(50),
    denial_date DATE NOT NULL,
    denial_reason VARCHAR(200) NOT NULL,
    denial_code VARCHAR(50),
    amount_denied DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'new',
    priority INTEGER DEFAULT 0,
    appeal_deadline DATE,
    appeal_status VARCHAR(20),
    appeal_date DATE,
    resolution_date DATE,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_denial_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_denial_insurance FOREIGN KEY (insurance_id) REFERENCES insurance_types(id),
    CONSTRAINT chk_denial_dates CHECK (
        denial_date <= appeal_deadline OR appeal_deadline IS NULL
    ),
    CONSTRAINT chk_denial_amount CHECK (amount_denied >= 0)
);

CREATE TABLE IF NOT EXISTS denial_notes (
    id SERIAL PRIMARY KEY,
    denial_id INTEGER NOT NULL,
    note_type VARCHAR(50),
    note_text TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_denial_note FOREIGN KEY (denial_id) REFERENCES denials(id)
);

CREATE TABLE IF NOT EXISTS denial_attachments (
    id SERIAL PRIMARY KEY,
    denial_id INTEGER NOT NULL,
    file_attachment_id INTEGER NOT NULL,
    attachment_type VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_denial_attachment_denial FOREIGN KEY (denial_id) REFERENCES denials(id),
    CONSTRAINT fk_denial_attachment_file FOREIGN KEY (file_attachment_id) REFERENCES file_attachments(id)
);

-- Add indexes for better performance
CREATE INDEX idx_eligibility_customer ON eligibility_requests(customer_id);
CREATE INDEX idx_eligibility_insurance ON eligibility_requests(insurance_id);
CREATE INDEX idx_eligibility_dates ON eligibility_requests(request_date, response_date);
CREATE INDEX idx_eligibility_status ON eligibility_requests(status);
CREATE INDEX idx_eligibility_coverage ON eligibility_requests(coverage_start_date, coverage_end_date);

CREATE INDEX idx_denials_customer ON denials(customer_id);
CREATE INDEX idx_denials_insurance ON denials(insurance_id);
CREATE INDEX idx_denials_claim ON denials(claim_number);
CREATE INDEX idx_denials_dates ON denials(denial_date, appeal_deadline, resolution_date);
CREATE INDEX idx_denials_status ON denials(status);
CREATE INDEX idx_denials_appeal ON denials(appeal_status);

CREATE INDEX idx_denial_notes_denial ON denial_notes(denial_id);
CREATE INDEX idx_denial_notes_type ON denial_notes(note_type);

CREATE INDEX idx_denial_attachments_denial ON denial_attachments(denial_id);
CREATE INDEX idx_denial_attachments_type ON denial_attachments(attachment_type);

-- Add comments for documentation
COMMENT ON TABLE eligibility_requests IS 'Insurance eligibility verification requests and responses';
COMMENT ON TABLE denials IS 'Insurance claim denials tracking';
COMMENT ON TABLE denial_notes IS 'Notes related to denial cases';
COMMENT ON TABLE denial_attachments IS 'File attachments for denial cases';

COMMIT;
