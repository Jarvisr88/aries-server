-- Migration Script - Level 3.2 (Additional CMN Form Tables)
-- Generated: 2024-12-19
-- Description: Creates remaining CMN form tables that depend on customers and medical_conditions

BEGIN;

-- Level 3.2: Additional CMN Form Tables
CREATE TABLE IF NOT EXISTS cmn_forms_0403b (
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
    CONSTRAINT fk_customer_0403b FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0403c (
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
    CONSTRAINT fk_customer_0403c FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0404c (
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
    CONSTRAINT fk_customer_0404c FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0602b (
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
    CONSTRAINT fk_customer_0602b FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_0603b (
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
    CONSTRAINT fk_customer_0603b FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Add indexes for better performance
CREATE INDEX idx_cmn_forms_0403b_customer ON cmn_forms_0403b(customer_id);
CREATE INDEX idx_cmn_forms_0403c_customer ON cmn_forms_0403c(customer_id);
CREATE INDEX idx_cmn_forms_0404c_customer ON cmn_forms_0404c(customer_id);
CREATE INDEX idx_cmn_forms_0602b_customer ON cmn_forms_0602b(customer_id);
CREATE INDEX idx_cmn_forms_0603b_customer ON cmn_forms_0603b(customer_id);

CREATE INDEX idx_cmn_forms_0403b_medical ON cmn_forms_0403b(medical_condition_id);
CREATE INDEX idx_cmn_forms_0403c_medical ON cmn_forms_0403c(medical_condition_id);
CREATE INDEX idx_cmn_forms_0404c_medical ON cmn_forms_0404c(medical_condition_id);
CREATE INDEX idx_cmn_forms_0602b_medical ON cmn_forms_0602b(medical_condition_id);
CREATE INDEX idx_cmn_forms_0603b_medical ON cmn_forms_0603b(medical_condition_id);

-- Add comments for documentation
COMMENT ON TABLE cmn_forms_0403b IS 'CMN Form Type 04.03 Part B';
COMMENT ON TABLE cmn_forms_0403c IS 'CMN Form Type 04.03 Part C';
COMMENT ON TABLE cmn_forms_0404c IS 'CMN Form Type 04.04 Part C';
COMMENT ON TABLE cmn_forms_0602b IS 'CMN Form Type 06.02 Part B';
COMMENT ON TABLE cmn_forms_0603b IS 'CMN Form Type 06.03 Part B';

COMMIT;
