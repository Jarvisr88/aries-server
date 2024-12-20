-- Migration Script - Level 3.3 (Additional CMN Form Tables)
-- Generated: 2024-12-19
-- Description: Creates remaining CMN form tables that depend on customers and medical_conditions

BEGIN;

-- Level 3.3: Additional CMN Form Tables
CREATE TABLE IF NOT EXISTS cmn_forms_0702a (
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
    CONSTRAINT fk_customer_0702a FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0702b (
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
    CONSTRAINT fk_customer_0702b FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0703a (
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
    CONSTRAINT fk_customer_0703a FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0802 (
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
    CONSTRAINT fk_customer_0802 FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0902 (
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
    CONSTRAINT fk_customer_0902 FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Add indexes for better performance
CREATE INDEX idx_cmn_forms_0702a_customer ON cmn_forms_0702a(customer_id);
CREATE INDEX idx_cmn_forms_0702b_customer ON cmn_forms_0702b(customer_id);
CREATE INDEX idx_cmn_forms_0703a_customer ON cmn_forms_0703a(customer_id);
CREATE INDEX idx_cmn_forms_0802_customer ON cmn_forms_0802(customer_id);
CREATE INDEX idx_cmn_forms_0902_customer ON cmn_forms_0902(customer_id);

CREATE INDEX idx_cmn_forms_0702a_medical ON cmn_forms_0702a(medical_condition_id);
CREATE INDEX idx_cmn_forms_0702b_medical ON cmn_forms_0702b(medical_condition_id);
CREATE INDEX idx_cmn_forms_0703a_medical ON cmn_forms_0703a(medical_condition_id);
CREATE INDEX idx_cmn_forms_0802_medical ON cmn_forms_0802(medical_condition_id);
CREATE INDEX idx_cmn_forms_0902_medical ON cmn_forms_0902(medical_condition_id);

-- Add comments for documentation
COMMENT ON TABLE cmn_forms_0702a IS 'CMN Form Type 07.02 Part A';
COMMENT ON TABLE cmn_forms_0702b IS 'CMN Form Type 07.02 Part B';
COMMENT ON TABLE cmn_forms_0703a IS 'CMN Form Type 07.03 Part A';
COMMENT ON TABLE cmn_forms_0802 IS 'CMN Form Type 08.02';
COMMENT ON TABLE cmn_forms_0902 IS 'CMN Form Type 09.02';

COMMIT;
