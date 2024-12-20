-- Migration Script - Level 4.28 (Variables and Settings)
-- Generated: 2024-12-19
-- Description: Creates tables for system variables, settings, and configurations

BEGIN;

-- Drop existing tables
DROP TABLE IF EXISTS variable_history CASCADE;
DROP TABLE IF EXISTS variable_values CASCADE;
DROP TABLE IF EXISTS variable_definitions CASCADE;
DROP TABLE IF EXISTS setting_history CASCADE;
DROP TABLE IF EXISTS setting_values CASCADE;
DROP TABLE IF EXISTS setting_definitions CASCADE;
DROP TABLE IF EXISTS configuration_history CASCADE;
DROP TABLE IF EXISTS configuration_values CASCADE;
DROP TABLE IF EXISTS configuration_definitions CASCADE;

-- Create variable tables
CREATE TABLE variable_definitions (
    id SERIAL PRIMARY KEY,
    variable_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    data_type VARCHAR(50) NOT NULL,
    default_value TEXT,
    validation_rules JSONB,
    is_system BOOLEAN DEFAULT false,
    is_required BOOLEAN DEFAULT false,
    is_encrypted BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT chk_variable_type CHECK (
        data_type IN ('string', 'number', 'boolean', 'date', 'json', 'array')
    )
);

CREATE TABLE variable_values (
    id SERIAL PRIMARY KEY,
    definition_id INTEGER NOT NULL REFERENCES variable_definitions(id),
    entity_type VARCHAR(50),
    entity_id INTEGER,
    value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

CREATE TABLE variable_history (
    id SERIAL PRIMARY KEY,
    value_id INTEGER NOT NULL REFERENCES variable_values(id),
    old_value TEXT,
    new_value TEXT,
    change_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(50),
    change_reason TEXT,
    metadata JSONB
);

-- Create setting tables
CREATE TABLE setting_definitions (
    id SERIAL PRIMARY KEY,
    setting_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),
    data_type VARCHAR(50) NOT NULL,
    default_value TEXT,
    allowed_values JSONB,
    is_system BOOLEAN DEFAULT false,
    is_required BOOLEAN DEFAULT false,
    is_readonly BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT chk_setting_type CHECK (
        data_type IN ('string', 'number', 'boolean', 'date', 'json', 'array')
    )
);

CREATE TABLE setting_values (
    id SERIAL PRIMARY KEY,
    definition_id INTEGER NOT NULL REFERENCES setting_definitions(id),
    value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

CREATE TABLE setting_history (
    id SERIAL PRIMARY KEY,
    value_id INTEGER NOT NULL REFERENCES setting_values(id),
    old_value TEXT,
    new_value TEXT,
    change_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(50),
    change_reason TEXT,
    metadata JSONB
);

-- Create configuration tables
CREATE TABLE configuration_definitions (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    module VARCHAR(50),
    data_type VARCHAR(50) NOT NULL,
    default_value TEXT,
    validation_rules JSONB,
    is_system BOOLEAN DEFAULT false,
    is_required BOOLEAN DEFAULT false,
    is_sensitive BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT chk_config_type CHECK (
        data_type IN ('string', 'number', 'boolean', 'date', 'json', 'array')
    )
);

CREATE TABLE configuration_values (
    id SERIAL PRIMARY KEY,
    definition_id INTEGER NOT NULL REFERENCES configuration_definitions(id),
    environment VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

CREATE TABLE configuration_history (
    id SERIAL PRIMARY KEY,
    value_id INTEGER NOT NULL REFERENCES configuration_values(id),
    old_value TEXT,
    new_value TEXT,
    change_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(50),
    change_reason TEXT,
    metadata JSONB
);

-- Create indexes
CREATE INDEX idx_var_def_name ON variable_definitions(variable_name);
CREATE INDEX idx_var_val_def ON variable_values(definition_id);
CREATE INDEX idx_var_hist_val ON variable_history(value_id);

CREATE INDEX idx_set_def_name ON setting_definitions(setting_name);
CREATE INDEX idx_set_val_def ON setting_values(definition_id);
CREATE INDEX idx_set_hist_val ON setting_history(value_id);

CREATE INDEX idx_cfg_def_name ON configuration_definitions(config_name);
CREATE INDEX idx_cfg_val_def ON configuration_values(definition_id);
CREATE INDEX idx_cfg_hist_val ON configuration_history(value_id);

COMMIT;
