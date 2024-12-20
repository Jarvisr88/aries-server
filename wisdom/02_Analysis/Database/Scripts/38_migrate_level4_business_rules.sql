-- Migration Script - Level 4.22 (Business Rules and Validation)
-- Generated: 2024-12-19
-- Description: Creates business rules, validation rules, and data quality tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS validation_rule_executions CASCADE;
DROP TABLE IF EXISTS validation_rule_conditions CASCADE;
DROP TABLE IF EXISTS validation_rules CASCADE;
DROP TABLE IF EXISTS business_rule_actions CASCADE;
DROP TABLE IF EXISTS business_rule_conditions CASCADE;
DROP TABLE IF EXISTS business_rules CASCADE;
DROP TABLE IF EXISTS rule_categories CASCADE;

-- Level 4.65: Rule Categories and Definitions
CREATE TABLE IF NOT EXISTS rule_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER,
    rule_type VARCHAR(50) NOT NULL,
    display_order INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_rule_category_parent FOREIGN KEY (parent_id) REFERENCES rule_categories(id),
    CONSTRAINT uq_rule_category_name UNIQUE (name),
    CONSTRAINT chk_rule_category_type CHECK (
        rule_type IN ('business', 'validation', 'both')
    )
);

CREATE TABLE IF NOT EXISTS business_rules (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    entity_type VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 0,
    execution_order INTEGER,
    is_active BOOLEAN DEFAULT true,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_business_rule_category FOREIGN KEY (category_id) REFERENCES rule_categories(id),
    CONSTRAINT uq_business_rule_name UNIQUE (name),
    CONSTRAINT chk_business_rule_dates CHECK (
        start_date <= end_date OR end_date IS NULL
    )
);

-- Level 4.66: Business Rule Components
CREATE TABLE IF NOT EXISTS business_rule_conditions (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL,
    condition_type VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    operator VARCHAR(50) NOT NULL,
    value_type VARCHAR(50) NOT NULL,
    comparison_value TEXT,
    sequence_order INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_business_rule_condition_rule FOREIGN KEY (rule_id) REFERENCES business_rules(id),
    CONSTRAINT chk_business_rule_condition_operator CHECK (
        operator IN ('equals', 'not_equals', 'greater_than', 'less_than', 'contains', 'not_contains', 
                    'in', 'not_in', 'between', 'regex', 'is_null', 'is_not_null')
    ),
    CONSTRAINT chk_business_rule_value_type CHECK (
        value_type IN ('string', 'number', 'boolean', 'date', 'array', 'object')
    )
);

CREATE TABLE IF NOT EXISTS business_rule_actions (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_field VARCHAR(100),
    action_value TEXT,
    parameters JSONB,
    sequence_order INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_business_rule_action_rule FOREIGN KEY (rule_id) REFERENCES business_rules(id),
    CONSTRAINT chk_business_rule_action_type CHECK (
        action_type IN ('update', 'insert', 'delete', 'notify', 'calculate', 'validate', 'custom')
    )
);

-- Level 4.67: Validation Rules
CREATE TABLE IF NOT EXISTS validation_rules (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    entity_type VARCHAR(50) NOT NULL,
    validation_type VARCHAR(50) NOT NULL,
    severity_level VARCHAR(20) DEFAULT 'error',
    is_blocking BOOLEAN DEFAULT true,
    error_message TEXT,
    resolution_hint TEXT,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_validation_rule_category FOREIGN KEY (category_id) REFERENCES rule_categories(id),
    CONSTRAINT uq_validation_rule_name UNIQUE (name),
    CONSTRAINT chk_validation_severity CHECK (
        severity_level IN ('info', 'warning', 'error', 'critical')
    ),
    CONSTRAINT chk_validation_type CHECK (
        validation_type IN ('format', 'range', 'required', 'unique', 'reference', 'custom')
    )
);

CREATE TABLE IF NOT EXISTS validation_rule_conditions (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    condition_type VARCHAR(50) NOT NULL,
    operator VARCHAR(50) NOT NULL,
    expected_value TEXT,
    custom_validation TEXT,
    sequence_order INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_validation_rule_condition_rule FOREIGN KEY (rule_id) REFERENCES validation_rules(id),
    CONSTRAINT chk_validation_condition_type CHECK (
        condition_type IN ('format', 'range', 'required', 'unique', 'reference', 'custom')
    )
);

CREATE TABLE IF NOT EXISTS validation_rule_executions (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    validation_status VARCHAR(20) NOT NULL,
    error_message TEXT,
    validation_details JSONB,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_by VARCHAR(50),
    CONSTRAINT fk_validation_execution_rule FOREIGN KEY (rule_id) REFERENCES validation_rules(id),
    CONSTRAINT chk_validation_execution_status CHECK (
        validation_status IN ('passed', 'failed', 'warning', 'error')
    )
);

-- Add indexes for better performance
CREATE INDEX idx_rule_categories_parent ON rule_categories(parent_id);
CREATE INDEX idx_rule_categories_type ON rule_categories(rule_type);
CREATE INDEX idx_rule_categories_active ON rule_categories(is_active);

CREATE INDEX idx_business_rules_category ON business_rules(category_id);
CREATE INDEX idx_business_rules_entity ON business_rules(entity_type);
CREATE INDEX idx_business_rules_priority ON business_rules(priority);
CREATE INDEX idx_business_rules_active ON business_rules(is_active);
CREATE INDEX idx_business_rules_dates ON business_rules(start_date, end_date);

CREATE INDEX idx_business_rule_conditions_rule ON business_rule_conditions(rule_id);
CREATE INDEX idx_business_rule_conditions_type ON business_rule_conditions(condition_type);
CREATE INDEX idx_business_rule_conditions_field ON business_rule_conditions(field_name);
CREATE INDEX idx_business_rule_conditions_active ON business_rule_conditions(is_active);

CREATE INDEX idx_business_rule_actions_rule ON business_rule_actions(rule_id);
CREATE INDEX idx_business_rule_actions_type ON business_rule_actions(action_type);
CREATE INDEX idx_business_rule_actions_target ON business_rule_actions(target_type, target_field);
CREATE INDEX idx_business_rule_actions_active ON business_rule_actions(is_active);

CREATE INDEX idx_validation_rules_category ON validation_rules(category_id);
CREATE INDEX idx_validation_rules_entity ON validation_rules(entity_type);
CREATE INDEX idx_validation_rules_type ON validation_rules(validation_type);
CREATE INDEX idx_validation_rules_severity ON validation_rules(severity_level);
CREATE INDEX idx_validation_rules_active ON validation_rules(is_active);

CREATE INDEX idx_validation_rule_conditions_rule ON validation_rule_conditions(rule_id);
CREATE INDEX idx_validation_rule_conditions_field ON validation_rule_conditions(field_name);
CREATE INDEX idx_validation_rule_conditions_type ON validation_rule_conditions(condition_type);
CREATE INDEX idx_validation_rule_conditions_active ON validation_rule_conditions(is_active);

CREATE INDEX idx_validation_executions_rule ON validation_rule_executions(rule_id);
CREATE INDEX idx_validation_executions_entity ON validation_rule_executions(entity_type, entity_id);
CREATE INDEX idx_validation_executions_status ON validation_rule_executions(validation_status);
CREATE INDEX idx_validation_executions_date ON validation_rule_executions(executed_at);

-- Add comments for documentation
COMMENT ON TABLE rule_categories IS 'Categories for business and validation rules';
COMMENT ON TABLE business_rules IS 'Business rule definitions';
COMMENT ON TABLE business_rule_conditions IS 'Conditions for business rules';
COMMENT ON TABLE business_rule_actions IS 'Actions to be taken when business rules are triggered';
COMMENT ON TABLE validation_rules IS 'Data validation rule definitions';
COMMENT ON TABLE validation_rule_conditions IS 'Conditions for validation rules';
COMMENT ON TABLE validation_rule_executions IS 'Validation rule execution history';

COMMIT;
