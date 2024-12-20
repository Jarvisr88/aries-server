-- Migration Script - Level 4.26 (Insurance and Payment Management)
-- Generated: 2024-12-19
-- Description: Creates tables for insurance, payment plans, deposits, and denials

DO $$ 
BEGIN

-- Drop existing tables if they exist
DROP TABLE IF EXISTS denial_reasons CASCADE;
DROP TABLE IF EXISTS claim_denials CASCADE;
DROP TABLE IF EXISTS deposit_details CASCADE;
DROP TABLE IF EXISTS deposits CASCADE;
DROP TABLE IF EXISTS payment_plan_items CASCADE;
DROP TABLE IF EXISTS payment_plans CASCADE;
DROP TABLE IF EXISTS insurance_authorizations CASCADE;
DROP TABLE IF EXISTS insurance_claims CASCADE;
DROP TABLE IF EXISTS insurance_coverage CASCADE;
DROP TABLE IF EXISTS insurance_policies CASCADE;
DROP TABLE IF EXISTS insurance_payers CASCADE;

-- Create insurance tables
CREATE TABLE IF NOT EXISTS insurance_payers (
    id SERIAL PRIMARY KEY,
    payer_code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50),
    contact_info JSONB,
    billing_info JSONB,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_payer_code UNIQUE (payer_code)
);

CREATE TABLE IF NOT EXISTS insurance_policies (
    id SERIAL PRIMARY KEY,
    payer_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    policy_number VARCHAR(100) NOT NULL,
    group_number VARCHAR(100),
    policy_holder JSONB,
    coverage_start_date DATE NOT NULL,
    coverage_end_date DATE,
    policy_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    verification_status VARCHAR(20),
    verification_date TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_policy_payer FOREIGN KEY (payer_id) REFERENCES insurance_payers(id),
    CONSTRAINT fk_policy_patient FOREIGN KEY (patient_id) REFERENCES patients(id),
    CONSTRAINT chk_policy_status CHECK (
        status IN ('active', 'inactive', 'expired', 'cancelled')
    ),
    CONSTRAINT chk_verification_status CHECK (
        verification_status IN ('pending', 'verified', 'failed', 'expired')
    )
);

CREATE TABLE IF NOT EXISTS insurance_coverage (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER NOT NULL,
    coverage_type VARCHAR(50) NOT NULL,
    benefit_details JSONB,
    copay_amount DECIMAL(10,2),
    coinsurance_rate DECIMAL(5,2),
    deductible_amount DECIMAL(10,2),
    out_of_pocket_max DECIMAL(10,2),
    prior_auth_required BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_coverage_policy FOREIGN KEY (policy_id) REFERENCES insurance_policies(id)
);

CREATE TABLE IF NOT EXISTS insurance_claims (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER NOT NULL,
    claim_number VARCHAR(100) NOT NULL,
    service_date DATE NOT NULL,
    filing_date DATE NOT NULL,
    diagnosis_codes TEXT[],
    procedure_codes TEXT[],
    claim_amount DECIMAL(10,2) NOT NULL,
    approved_amount DECIMAL(10,2),
    paid_amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'submitted',
    adjudication_date DATE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_claim_policy FOREIGN KEY (policy_id) REFERENCES insurance_policies(id),
    CONSTRAINT uq_claim_number UNIQUE (claim_number),
    CONSTRAINT chk_claim_status CHECK (
        status IN ('draft', 'submitted', 'pending', 'approved', 'paid', 'denied', 'appealed')
    )
);

CREATE TABLE IF NOT EXISTS insurance_authorizations (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER NOT NULL,
    auth_number VARCHAR(100) NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    authorized_units INTEGER,
    used_units INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_auth_policy FOREIGN KEY (policy_id) REFERENCES insurance_policies(id),
    CONSTRAINT uq_auth_number UNIQUE (auth_number),
    CONSTRAINT chk_auth_status CHECK (
        status IN ('pending', 'active', 'expired', 'cancelled')
    )
);

-- Create payment plan tables
CREATE TABLE IF NOT EXISTS payment_plans (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    down_payment DECIMAL(10,2),
    number_of_payments INTEGER NOT NULL,
    payment_frequency VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_plan_patient FOREIGN KEY (patient_id) REFERENCES patients(id),
    CONSTRAINT chk_plan_status CHECK (
        status IN ('draft', 'active', 'completed', 'defaulted', 'cancelled')
    ),
    CONSTRAINT chk_payment_frequency CHECK (
        payment_frequency IN ('weekly', 'biweekly', 'monthly', 'quarterly')
    )
);

CREATE TABLE IF NOT EXISTS payment_plan_items (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    paid_amount DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    paid_date DATE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_plan_item_plan FOREIGN KEY (plan_id) REFERENCES payment_plans(id),
    CONSTRAINT chk_plan_item_status CHECK (
        status IN ('pending', 'partial', 'paid', 'late', 'defaulted')
    )
);

-- Create deposit tables
CREATE TABLE IF NOT EXISTS deposits (
    id SERIAL PRIMARY KEY,
    deposit_date DATE NOT NULL,
    deposit_number VARCHAR(50) NOT NULL,
    bank_account VARCHAR(100) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_deposit_number UNIQUE (deposit_number),
    CONSTRAINT chk_deposit_status CHECK (
        status IN ('pending', 'completed', 'reconciled', 'voided')
    )
);

CREATE TABLE IF NOT EXISTS deposit_details (
    id SERIAL PRIMARY KEY,
    deposit_id INTEGER NOT NULL,
    payment_type VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(100),
    amount DECIMAL(10,2) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_deposit_detail_deposit FOREIGN KEY (deposit_id) REFERENCES deposits(id),
    CONSTRAINT chk_payment_type CHECK (
        payment_type IN ('cash', 'check', 'credit_card', 'ach', 'other')
    )
);

-- Create denial tables
CREATE TABLE IF NOT EXISTS denial_reasons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_denial_reason_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS claim_denials (
    id SERIAL PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    reason_id INTEGER NOT NULL,
    denial_date DATE NOT NULL,
    appeal_deadline DATE,
    appeal_status VARCHAR(20),
    appeal_date DATE,
    resolution_date DATE,
    resolution_notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_denial_claim FOREIGN KEY (claim_id) REFERENCES insurance_claims(id),
    CONSTRAINT fk_denial_reason FOREIGN KEY (reason_id) REFERENCES denial_reasons(id),
    CONSTRAINT chk_appeal_status CHECK (
        appeal_status IN ('pending', 'submitted', 'approved', 'denied', 'expired')
    )
);

-- Add indexes for better performance
CREATE INDEX idx_insurance_payers_code ON insurance_payers(payer_code);
CREATE INDEX idx_insurance_payers_active ON insurance_payers(is_active);

CREATE INDEX idx_insurance_policies_payer ON insurance_policies(payer_id);
CREATE INDEX idx_insurance_policies_patient ON insurance_policies(patient_id);
CREATE INDEX idx_insurance_policies_status ON insurance_policies(status);
CREATE INDEX idx_insurance_policies_dates ON insurance_policies(coverage_start_date, coverage_end_date);

CREATE INDEX idx_insurance_coverage_policy ON insurance_coverage(policy_id);
CREATE INDEX idx_insurance_coverage_type ON insurance_coverage(coverage_type);

CREATE INDEX idx_insurance_claims_policy ON insurance_claims(policy_id);
CREATE INDEX idx_insurance_claims_number ON insurance_claims(claim_number);
CREATE INDEX idx_insurance_claims_dates ON insurance_claims(service_date, filing_date);
CREATE INDEX idx_insurance_claims_status ON insurance_claims(status);

CREATE INDEX idx_insurance_auth_policy ON insurance_authorizations(policy_id);
CREATE INDEX idx_insurance_auth_number ON insurance_authorizations(auth_number);
CREATE INDEX idx_insurance_auth_dates ON insurance_authorizations(start_date, end_date);
CREATE INDEX idx_insurance_auth_status ON insurance_authorizations(status);

CREATE INDEX idx_payment_plans_patient ON payment_plans(patient_id);
CREATE INDEX idx_payment_plans_dates ON payment_plans(start_date, end_date);
CREATE INDEX idx_payment_plans_status ON payment_plans(status);

CREATE INDEX idx_payment_plan_items_plan ON payment_plan_items(plan_id);
CREATE INDEX idx_payment_plan_items_dates ON payment_plan_items(due_date);
CREATE INDEX idx_payment_plan_items_status ON payment_plan_items(status);

CREATE INDEX idx_deposits_date ON deposits(deposit_date);
CREATE INDEX idx_deposits_number ON deposits(deposit_number);
CREATE INDEX idx_deposits_status ON deposits(status);

CREATE INDEX idx_deposit_details_deposit ON deposit_details(deposit_id);
CREATE INDEX idx_deposit_details_type ON deposit_details(payment_type);

CREATE INDEX idx_denial_reasons_code ON denial_reasons(code);
CREATE INDEX idx_denial_reasons_category ON denial_reasons(category);
CREATE INDEX idx_denial_reasons_active ON denial_reasons(is_active);

CREATE INDEX idx_claim_denials_claim ON claim_denials(claim_id);
CREATE INDEX idx_claim_denials_reason ON claim_denials(reason_id);
CREATE INDEX idx_claim_denials_dates ON claim_denials(denial_date, appeal_deadline);
CREATE INDEX idx_claim_denials_status ON claim_denials(appeal_status);

EXCEPTION WHEN OTHERS THEN
    -- Roll back the transaction on error
    RAISE NOTICE 'Error occurred: %', SQLERRM;
    RAISE EXCEPTION 'Transaction aborted';
END;
$$ LANGUAGE plpgsql;
