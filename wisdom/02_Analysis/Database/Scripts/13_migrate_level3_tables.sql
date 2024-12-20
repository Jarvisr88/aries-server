-- Migration Script - Level 3 (Tables with Level 2 Dependencies)
-- Generated: 2024-12-19
-- Description: Creates tables that depend on Level 2 tables and customers table

BEGIN;

-- Level 3.1: CMN Form Tables (depends on customers)
CREATE TABLE IF NOT EXISTS cmn_forms_0102a (
    id SERIAL PRIMARY KEY,
    form_id INTEGER NOT NULL,
    form_type VARCHAR(10) NOT NULL,
    customer_id INTEGER NOT NULL,
    medical_condition_id INTEGER REFERENCES medical_conditions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    status VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    form_data JSONB,
    CONSTRAINT fk_customer_0102a FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0102b (
    id SERIAL PRIMARY KEY,
    form_id INTEGER NOT NULL,
    form_type VARCHAR(10) NOT NULL,
    customer_id INTEGER NOT NULL,
    medical_condition_id INTEGER REFERENCES medical_conditions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    status VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    form_data JSONB,
    CONSTRAINT fk_customer_0102b FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0203a (
    id SERIAL PRIMARY KEY,
    form_id INTEGER NOT NULL,
    form_type VARCHAR(10) NOT NULL,
    customer_id INTEGER NOT NULL,
    medical_condition_id INTEGER REFERENCES medical_conditions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    status VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    form_data JSONB,
    CONSTRAINT fk_customer_0203a FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0203b (
    id SERIAL PRIMARY KEY,
    form_id INTEGER NOT NULL,
    form_type VARCHAR(10) NOT NULL,
    customer_id INTEGER NOT NULL,
    medical_condition_id INTEGER REFERENCES medical_conditions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    status VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    form_data JSONB,
    CONSTRAINT fk_customer_0203b FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0302 (
    id SERIAL PRIMARY KEY,
    form_id INTEGER NOT NULL,
    form_type VARCHAR(10) NOT NULL,
    customer_id INTEGER NOT NULL,
    medical_condition_id INTEGER REFERENCES medical_conditions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    status VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    form_data JSONB,
    CONSTRAINT fk_customer_0302 FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Add indexes for better performance
CREATE INDEX idx_cmn_forms_0102a_customer ON cmn_forms_0102a(customer_id);
CREATE INDEX idx_cmn_forms_0102b_customer ON cmn_forms_0102b(customer_id);
CREATE INDEX idx_cmn_forms_0203a_customer ON cmn_forms_0203a(customer_id);
CREATE INDEX idx_cmn_forms_0203b_customer ON cmn_forms_0203b(customer_id);
CREATE INDEX idx_cmn_forms_0302_customer ON cmn_forms_0302(customer_id);

CREATE INDEX idx_cmn_forms_0102a_medical ON cmn_forms_0102a(medical_condition_id);
CREATE INDEX idx_cmn_forms_0102b_medical ON cmn_forms_0102b(medical_condition_id);
CREATE INDEX idx_cmn_forms_0203a_medical ON cmn_forms_0203a(medical_condition_id);
CREATE INDEX idx_cmn_forms_0203b_medical ON cmn_forms_0203b(medical_condition_id);
CREATE INDEX idx_cmn_forms_0302_medical ON cmn_forms_0302(medical_condition_id);

-- Add comments for documentation
COMMENT ON TABLE cmn_forms_0102a IS 'CMN Form Type 01.02 Part A';
COMMENT ON TABLE cmn_forms_0102b IS 'CMN Form Type 01.02 Part B';
COMMENT ON TABLE cmn_forms_0203a IS 'CMN Form Type 02.03 Part A';
COMMENT ON TABLE cmn_forms_0203b IS 'CMN Form Type 02.03 Part B';
COMMENT ON TABLE cmn_forms_0302 IS 'CMN Form Type 03.02';

COMMIT;
