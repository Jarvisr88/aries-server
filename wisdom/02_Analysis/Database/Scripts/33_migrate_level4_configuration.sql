-- Migration Script - Level 4.17 (System Configuration)
-- Generated: 2024-12-19
-- Description: Creates system configuration and settings management tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS feature_flags CASCADE;
DROP TABLE IF EXISTS system_variables CASCADE;
DROP TABLE IF EXISTS configuration_history CASCADE;
DROP TABLE IF EXISTS system_modules CASCADE;
DROP TABLE IF EXISTS environment_settings CASCADE;

-- Level 4.48: System Modules
CREATE TABLE IF NOT EXISTS system_modules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    version VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',
    dependencies JSONB,
    settings JSONB,
    is_core BOOLEAN DEFAULT false,
    is_enabled BOOLEAN DEFAULT true,
    install_date TIMESTAMP,
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_system_module_name UNIQUE (name),
    CONSTRAINT chk_system_module_status CHECK (
        status IN ('active', 'inactive', 'error', 'updating')
    )
);

-- Level 4.49: Environment Configuration
CREATE TABLE IF NOT EXISTS environment_settings (
    id SERIAL PRIMARY KEY,
    environment VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    data_type VARCHAR(20) NOT NULL,
    is_encrypted BOOLEAN DEFAULT false,
    description TEXT,
    is_editable BOOLEAN DEFAULT true,
    validation_rules JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_environment_setting UNIQUE (environment, category, setting_key),
    CONSTRAINT chk_environment_setting_type CHECK (
        data_type IN ('string', 'number', 'boolean', 'json', 'array')
    )
);

-- Level 4.50: System Variables
CREATE TABLE IF NOT EXISTS system_variables (
    id SERIAL PRIMARY KEY,
    module_id INTEGER,
    name VARCHAR(100) NOT NULL,
    value TEXT,
    data_type VARCHAR(20) NOT NULL,
    is_runtime_configurable BOOLEAN DEFAULT false,
    requires_restart BOOLEAN DEFAULT false,
    description TEXT,
    validation_rules JSONB,
    default_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_system_variable_module FOREIGN KEY (module_id) REFERENCES system_modules(id),
    CONSTRAINT uq_system_variable_name UNIQUE (module_id, name),
    CONSTRAINT chk_system_variable_type CHECK (
        data_type IN ('string', 'number', 'boolean', 'json', 'array')
    )
);

-- Level 4.51: Feature Flags
CREATE TABLE IF NOT EXISTS feature_flags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT false,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    percentage_rollout INTEGER,
    rules JSONB,
    dependencies JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_feature_flag_name UNIQUE (name),
    CONSTRAINT chk_feature_flag_dates CHECK (
        start_date IS NULL OR end_date IS NULL OR start_date <= end_date
    ),
    CONSTRAINT chk_feature_flag_rollout CHECK (
        percentage_rollout IS NULL OR 
        (percentage_rollout >= 0 AND percentage_rollout <= 100)
    )
);

-- Level 4.52: Configuration History
CREATE TABLE IF NOT EXISTS configuration_history (
    id SERIAL PRIMARY KEY,
    config_type VARCHAR(50) NOT NULL,
    config_id INTEGER NOT NULL,
    change_type VARCHAR(20) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    reason TEXT,
    change_source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    CONSTRAINT chk_config_history_type CHECK (
        config_type IN ('module', 'environment', 'variable', 'feature')
    ),
    CONSTRAINT chk_config_history_change CHECK (
        change_type IN ('create', 'update', 'delete', 'enable', 'disable')
    )
);

-- Add indexes for better performance
CREATE INDEX idx_system_modules_status ON system_modules(status);
CREATE INDEX idx_system_modules_enabled ON system_modules(is_enabled);
CREATE INDEX idx_system_modules_core ON system_modules(is_core);

CREATE INDEX idx_environment_settings_env ON environment_settings(environment);
CREATE INDEX idx_environment_settings_category ON environment_settings(category);
CREATE INDEX idx_environment_settings_editable ON environment_settings(is_editable);

CREATE INDEX idx_system_variables_module ON system_variables(module_id);
CREATE INDEX idx_system_variables_configurable ON system_variables(is_runtime_configurable);
CREATE INDEX idx_system_variables_restart ON system_variables(requires_restart);

CREATE INDEX idx_feature_flags_enabled ON feature_flags(is_enabled);
CREATE INDEX idx_feature_flags_dates ON feature_flags(start_date, end_date);

CREATE INDEX idx_configuration_history_type ON configuration_history(config_type, config_id);
CREATE INDEX idx_configuration_history_change ON configuration_history(change_type);
CREATE INDEX idx_configuration_history_date ON configuration_history(created_at);

-- Add comments for documentation
COMMENT ON TABLE system_modules IS 'System module registry and configuration';
COMMENT ON TABLE environment_settings IS 'Environment-specific configuration settings';
COMMENT ON TABLE system_variables IS 'System-wide variable configuration';
COMMENT ON TABLE feature_flags IS 'Feature flag management';
COMMENT ON TABLE configuration_history IS 'Configuration change history';

-- Add trigger for configuration history tracking
CREATE OR REPLACE FUNCTION track_configuration_changes()
RETURNS TRIGGER AS $$
DECLARE
    config_type VARCHAR(50);
    change_type VARCHAR(20);
    old_value JSONB;
    new_value JSONB;
BEGIN
    -- Determine configuration type
    CASE TG_TABLE_NAME
        WHEN 'system_modules' THEN config_type := 'module';
        WHEN 'environment_settings' THEN config_type := 'environment';
        WHEN 'system_variables' THEN config_type := 'variable';
        WHEN 'feature_flags' THEN config_type := 'feature';
    END CASE;

    -- Determine change type
    IF TG_OP = 'INSERT' THEN
        change_type := 'create';
        old_value := NULL;
        new_value := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        change_type := 'update';
        old_value := to_jsonb(OLD);
        new_value := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        change_type := 'delete';
        old_value := to_jsonb(OLD);
        new_value := NULL;
    END IF;

    -- Record the change
    INSERT INTO configuration_history (
        config_type,
        config_id,
        change_type,
        old_value,
        new_value,
        created_by
    ) VALUES (
        config_type,
        CASE TG_OP
            WHEN 'DELETE' THEN OLD.id
            ELSE NEW.id
        END,
        change_type,
        old_value,
        new_value,
        CASE TG_OP
            WHEN 'DELETE' THEN OLD.updated_by
            ELSE NEW.updated_by
        END
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for configuration tracking
CREATE TRIGGER track_module_changes
    AFTER INSERT OR UPDATE OR DELETE ON system_modules
    FOR EACH ROW
    EXECUTE FUNCTION track_configuration_changes();

CREATE TRIGGER track_environment_changes
    AFTER INSERT OR UPDATE OR DELETE ON environment_settings
    FOR EACH ROW
    EXECUTE FUNCTION track_configuration_changes();

CREATE TRIGGER track_variable_changes
    AFTER INSERT OR UPDATE OR DELETE ON system_variables
    FOR EACH ROW
    EXECUTE FUNCTION track_configuration_changes();

CREATE TRIGGER track_feature_changes
    AFTER INSERT OR UPDATE OR DELETE ON feature_flags
    FOR EACH ROW
    EXECUTE FUNCTION track_configuration_changes();

COMMIT;
