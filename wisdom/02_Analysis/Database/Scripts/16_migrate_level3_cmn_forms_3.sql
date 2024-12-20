-- Migration Script - Level 3.4 (Final CMN Form Tables)
-- Generated: 2024-12-19
-- Description: Creates remaining CMN form tables that depend on customers and medical_conditions

BEGIN;

-- Level 3.4: Final CMN Form Tables
CREATE TABLE IF NOT EXISTS cmn_forms_0903 (
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
    CONSTRAINT fk_customer_0903 FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_1003 (
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
    CONSTRAINT fk_customer_1003 FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_4842 (
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
    CONSTRAINT fk_customer_4842 FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_drorder (
    id SERIAL PRIMARY KEY,
    form_id INTEGER NOT NULL,
    form_type VARCHAR(10) NOT NULL,
    customer_id INTEGER NOT NULL,
    medical_condition_id INTEGER REFERENCES medical_conditions(id),
    doctor_id INTEGER,  -- Will be linked to doctors table when created
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    status VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    form_data JSONB,
    CONSTRAINT fk_customer_drorder FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS cmn_forms_uro (
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
    CONSTRAINT fk_customer_uro FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Add indexes for better performance
CREATE INDEX idx_cmn_forms_0903_customer ON cmn_forms_0903(customer_id);
CREATE INDEX idx_cmn_forms_1003_customer ON cmn_forms_1003(customer_id);
CREATE INDEX idx_cmn_forms_4842_customer ON cmn_forms_4842(customer_id);
CREATE INDEX idx_cmn_forms_drorder_customer ON cmn_forms_drorder(customer_id);
CREATE INDEX idx_cmn_forms_uro_customer ON cmn_forms_uro(customer_id);

CREATE INDEX idx_cmn_forms_0903_medical ON cmn_forms_0903(medical_condition_id);
CREATE INDEX idx_cmn_forms_1003_medical ON cmn_forms_1003(medical_condition_id);
CREATE INDEX idx_cmn_forms_4842_medical ON cmn_forms_4842(medical_condition_id);
CREATE INDEX idx_cmn_forms_drorder_medical ON cmn_forms_drorder(medical_condition_id);
CREATE INDEX idx_cmn_forms_uro_medical ON cmn_forms_uro(medical_condition_id);

CREATE INDEX idx_cmn_forms_drorder_doctor ON cmn_forms_drorder(doctor_id);

-- Add comments for documentation
COMMENT ON TABLE cmn_forms_0903 IS 'CMN Form Type 09.03';
COMMENT ON TABLE cmn_forms_1003 IS 'CMN Form Type 10.03';
COMMENT ON TABLE cmn_forms_4842 IS 'CMN Form Type 4842';
COMMENT ON TABLE cmn_forms_drorder IS 'CMN Form Doctor Order Type';
COMMENT ON TABLE cmn_forms_uro IS 'CMN Form Urology Type';

COMMIT;
