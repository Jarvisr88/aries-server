-- Migration Script - Level 4.2 (Insurance and HAO Tables)
-- Generated: 2024-12-19
-- Description: Creates insurance-related tables

BEGIN;

-- Level 4.4: Insurance Company Groups
CREATE TABLE IF NOT EXISTS insurance_company_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_group_id INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_insurance_group_parent FOREIGN KEY (parent_group_id) REFERENCES insurance_company_groups(id)
);

-- Level 4.5: Health Account Organizations
CREATE TABLE IF NOT EXISTS health_account_organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    insurance_group_id INTEGER,
    organization_type VARCHAR(50),
    contract_number VARCHAR(50),
    contract_start_date DATE,
    contract_end_date DATE,
    billing_type VARCHAR(50),
    payment_terms VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_hao_insurance_group FOREIGN KEY (insurance_group_id) REFERENCES insurance_company_groups(id)
);

-- Level 4.6: Insurance Types and Details
CREATE TABLE IF NOT EXISTS insurance_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    coverage_type VARCHAR(50),
    is_primary BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

-- Level 4.7: Payer Information
CREATE TABLE IF NOT EXISTS payers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    insurance_group_id INTEGER,
    payer_type VARCHAR(50),
    payer_id VARCHAR(50),
    npi VARCHAR(10),
    tax_id VARCHAR(20),
    contact_name VARCHAR(100),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_payer_insurance_group FOREIGN KEY (insurance_group_id) REFERENCES insurance_company_groups(id)
);

-- Add indexes for better performance
CREATE INDEX idx_insurance_groups_parent ON insurance_company_groups(parent_group_id);
CREATE INDEX idx_insurance_groups_name ON insurance_company_groups(name);

CREATE INDEX idx_hao_insurance_group ON health_account_organizations(insurance_group_id);
CREATE INDEX idx_hao_contract ON health_account_organizations(contract_number);
CREATE INDEX idx_hao_dates ON health_account_organizations(contract_start_date, contract_end_date);

CREATE INDEX idx_insurance_types_name ON insurance_types(name);
CREATE INDEX idx_insurance_types_coverage ON insurance_types(coverage_type);

CREATE INDEX idx_payers_insurance_group ON payers(insurance_group_id);
CREATE INDEX idx_payers_ids ON payers(payer_id, npi, tax_id);
CREATE INDEX idx_payers_name ON payers(name);

-- Add comments for documentation
COMMENT ON TABLE insurance_company_groups IS 'Groups of insurance companies with hierarchical structure';
COMMENT ON TABLE health_account_organizations IS 'Health Account Organizations (HAOs) with contract details';
COMMENT ON TABLE insurance_types IS 'Types of insurance coverage available';
COMMENT ON TABLE payers IS 'Insurance payers and their identification details';

-- Add constraints for data integrity
ALTER TABLE health_account_organizations
    ADD CONSTRAINT chk_hao_contract_dates
    CHECK (contract_start_date <= contract_end_date OR contract_end_date IS NULL);

ALTER TABLE payers
    ADD CONSTRAINT chk_payer_npi
    CHECK (npi ~ '^\d{10}$' OR npi IS NULL);

COMMIT;
