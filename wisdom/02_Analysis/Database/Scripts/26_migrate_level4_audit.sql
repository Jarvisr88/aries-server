-- Migration Script - Level 4.10 (Audit and Activity Logging)
-- Generated: 2024-12-19
-- Description: Creates audit logging and activity tracking tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS audit_field_changes CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS activity_logs CASCADE;
DROP TABLE IF EXISTS activity_types CASCADE;

-- Level 4.26: Activity Types
CREATE TABLE IF NOT EXISTS activity_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    requires_notes BOOLEAN DEFAULT false,
    is_system_type BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_activity_type_name UNIQUE (name)
);

-- Level 4.27: Activity Logging
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    activity_type_id INTEGER NOT NULL,
    user_id INTEGER,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_activity_type FOREIGN KEY (activity_type_id) REFERENCES activity_types(id),
    CONSTRAINT fk_activity_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Level 4.28: Audit Logging
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_data JSONB,
    new_data JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_audit_action CHECK (action IN ('INSERT', 'UPDATE', 'DELETE'))
);

CREATE TABLE IF NOT EXISTS audit_field_changes (
    id SERIAL PRIMARY KEY,
    audit_log_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_type VARCHAR(20),
    CONSTRAINT fk_audit_field_log FOREIGN KEY (audit_log_id) REFERENCES audit_logs(id)
);

-- Add indexes for better performance
CREATE INDEX idx_activity_types_category ON activity_types(category);
CREATE INDEX idx_activity_types_name ON activity_types(name);

CREATE INDEX idx_activity_logs_type ON activity_logs(activity_type_id);
CREATE INDEX idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_entity ON activity_logs(entity_type, entity_id);
CREATE INDEX idx_activity_logs_action ON activity_logs(action);
CREATE INDEX idx_activity_logs_date ON activity_logs(created_at);

CREATE INDEX idx_audit_logs_table ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_record ON audit_logs(record_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_date ON audit_logs(timestamp);

CREATE INDEX idx_audit_field_changes_log ON audit_field_changes(audit_log_id);
CREATE INDEX idx_audit_field_changes_field ON audit_field_changes(field_name);

-- Add comments for documentation
COMMENT ON TABLE activity_types IS 'Predefined types of system activities';
COMMENT ON TABLE activity_logs IS 'User activity tracking';
COMMENT ON TABLE audit_logs IS 'System-wide audit logging';
COMMENT ON TABLE audit_field_changes IS 'Detailed field-level changes';

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_id INTEGER;
BEGIN
    -- Insert the audit log
    INSERT INTO audit_logs (
        table_name,
        record_id,
        action,
        user_id,
        old_data,
        new_data,
        ip_address
    ) VALUES (
        TG_TABLE_NAME,
        CASE 
            WHEN TG_OP = 'DELETE' THEN OLD.id
            ELSE NEW.id
        END,
        TG_OP,
        current_setting('app.current_user_id', TRUE)::INTEGER,
        CASE 
            WHEN TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN to_jsonb(OLD)
            ELSE NULL
        END,
        CASE 
            WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN to_jsonb(NEW)
            ELSE NULL
        END,
        current_setting('app.current_ip_address', TRUE)
    ) RETURNING id INTO audit_id;

    -- For updates, log the changed fields
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_field_changes (
            audit_log_id,
            field_name,
            old_value,
            new_value,
            change_type
        )
        SELECT 
            audit_id,
            key,
            old_value,
            new_value,
            CASE
                WHEN old_value IS NULL THEN 'added'
                WHEN new_value IS NULL THEN 'removed'
                ELSE 'modified'
            END
        FROM jsonb_each_text(to_jsonb(OLD)) old_fields
        FULL OUTER JOIN jsonb_each_text(to_jsonb(NEW)) new_fields USING (key)
        WHERE old_value IS DISTINCT FROM new_value;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

COMMIT;
