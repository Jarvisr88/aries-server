-- Migration Script - Level 4.15 (Reports and Analytics)
-- Generated: 2024-12-19
-- Description: Creates reporting, analytics, and data visualization tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS report_subscriptions CASCADE;
DROP TABLE IF EXISTS report_schedules CASCADE;
DROP TABLE IF EXISTS report_executions CASCADE;
DROP TABLE IF EXISTS report_parameters CASCADE;
DROP TABLE IF EXISTS report_definitions CASCADE;
DROP TABLE IF EXISTS report_categories CASCADE;

-- Level 4.42: Report Configuration
CREATE TABLE IF NOT EXISTS report_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_category_id INTEGER,
    display_order INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_report_category_parent FOREIGN KEY (parent_category_id) REFERENCES report_categories(id),
    CONSTRAINT uq_report_category_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS report_definitions (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) NOT NULL,
    data_source VARCHAR(100),
    query_definition TEXT,
    template_path VARCHAR(500),
    output_formats VARCHAR(50)[], -- Array of supported formats
    parameters JSONB,
    custom_logic TEXT,
    is_system_report BOOLEAN DEFAULT false,
    is_featured BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_report_definition_category FOREIGN KEY (category_id) REFERENCES report_categories(id),
    CONSTRAINT uq_report_definition_name UNIQUE (name)
);

-- Level 4.43: Report Parameters
CREATE TABLE IF NOT EXISTS report_parameters (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL,
    parameter_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    parameter_type VARCHAR(50) NOT NULL,
    default_value TEXT,
    is_required BOOLEAN DEFAULT false,
    validation_rules JSONB,
    display_order INTEGER,
    help_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_report_parameter_report FOREIGN KEY (report_id) REFERENCES report_definitions(id),
    CONSTRAINT uq_report_parameter_name UNIQUE (report_id, parameter_name)
);

-- Level 4.44: Report Execution
CREATE TABLE IF NOT EXISTS report_executions (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL,
    execution_id VARCHAR(50) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    parameters JSONB,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    output_format VARCHAR(20),
    output_size BIGINT,
    output_path VARCHAR(500),
    error_message TEXT,
    row_count INTEGER,
    execution_time INTEGER, -- in milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_report_execution_report FOREIGN KEY (report_id) REFERENCES report_definitions(id),
    CONSTRAINT fk_report_execution_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_report_execution_time CHECK (
        start_time <= end_time OR end_time IS NULL
    )
);

-- Level 4.45: Report Scheduling
CREATE TABLE IF NOT EXISTS report_schedules (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    schedule_type VARCHAR(50) NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    parameters JSONB,
    output_format VARCHAR(20) NOT NULL,
    recipients JSONB,
    is_active BOOLEAN DEFAULT true,
    last_run_time TIMESTAMP,
    next_run_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_report_schedule_report FOREIGN KEY (report_id) REFERENCES report_definitions(id),
    CONSTRAINT chk_report_schedule_dates CHECK (
        start_date <= end_date OR end_date IS NULL
    )
);

CREATE TABLE IF NOT EXISTS report_subscriptions (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    schedule_id INTEGER,
    subscription_type VARCHAR(50) NOT NULL,
    delivery_method VARCHAR(50) NOT NULL,
    format_preference VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    last_delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_report_subscription_report FOREIGN KEY (report_id) REFERENCES report_definitions(id),
    CONSTRAINT fk_report_subscription_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_report_subscription_schedule FOREIGN KEY (schedule_id) REFERENCES report_schedules(id),
    CONSTRAINT uq_report_subscription UNIQUE (report_id, user_id, subscription_type)
);

-- Add indexes for better performance
CREATE INDEX idx_report_categories_parent ON report_categories(parent_category_id);
CREATE INDEX idx_report_categories_active ON report_categories(is_active);

CREATE INDEX idx_report_definitions_category ON report_definitions(category_id);
CREATE INDEX idx_report_definitions_type ON report_definitions(report_type);
CREATE INDEX idx_report_definitions_active ON report_definitions(is_active);
CREATE INDEX idx_report_definitions_featured ON report_definitions(is_featured);

CREATE INDEX idx_report_parameters_report ON report_parameters(report_id);
CREATE INDEX idx_report_parameters_type ON report_parameters(parameter_type);

CREATE INDEX idx_report_executions_report ON report_executions(report_id);
CREATE INDEX idx_report_executions_user ON report_executions(user_id);
CREATE INDEX idx_report_executions_status ON report_executions(status);
CREATE INDEX idx_report_executions_dates ON report_executions(start_time, end_time);

CREATE INDEX idx_report_schedules_report ON report_schedules(report_id);
CREATE INDEX idx_report_schedules_dates ON report_schedules(start_date, end_date);
CREATE INDEX idx_report_schedules_next_run ON report_schedules(next_run_time);
CREATE INDEX idx_report_schedules_active ON report_schedules(is_active);

CREATE INDEX idx_report_subscriptions_report ON report_subscriptions(report_id);
CREATE INDEX idx_report_subscriptions_user ON report_subscriptions(user_id);
CREATE INDEX idx_report_subscriptions_schedule ON report_subscriptions(schedule_id);
CREATE INDEX idx_report_subscriptions_active ON report_subscriptions(is_active);

-- Add comments for documentation
COMMENT ON TABLE report_categories IS 'Report category hierarchy';
COMMENT ON TABLE report_definitions IS 'Report template definitions';
COMMENT ON TABLE report_parameters IS 'Report parameter configurations';
COMMENT ON TABLE report_executions IS 'Report execution history';
COMMENT ON TABLE report_schedules IS 'Report scheduling configuration';
COMMENT ON TABLE report_subscriptions IS 'User report subscriptions';

-- Add trigger for updating execution time
CREATE OR REPLACE FUNCTION calculate_execution_time()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.end_time IS NOT NULL AND NEW.start_time IS NOT NULL THEN
        NEW.execution_time = EXTRACT(EPOCH FROM (NEW.end_time - NEW.start_time)) * 1000;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_execution_time
    BEFORE UPDATE ON report_executions
    FOR EACH ROW
    EXECUTE FUNCTION calculate_execution_time();

COMMIT;
