-- Migration Script - Level 4.19 (Workflow Rules and Automation)
-- Generated: 2024-12-19
-- Description: Creates workflow, automation, and business process tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS workflow_executions CASCADE;
DROP TABLE IF EXISTS workflow_schedules CASCADE;
DROP TABLE IF EXISTS workflow_actions CASCADE;
DROP TABLE IF EXISTS workflow_conditions CASCADE;
DROP TABLE IF EXISTS workflow_triggers CASCADE;
DROP TABLE IF EXISTS workflow_definitions CASCADE;

-- Level 4.57: Workflow Definition
CREATE TABLE IF NOT EXISTS workflow_definitions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    version INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'draft',
    priority INTEGER DEFAULT 0,
    timeout INTEGER, -- in seconds
    retry_policy JSONB,
    error_handling JSONB,
    metadata JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_workflow_definition_name UNIQUE (name, version),
    CONSTRAINT chk_workflow_definition_status CHECK (
        status IN ('draft', 'active', 'deprecated', 'archived')
    )
);

-- Level 4.58: Workflow Components
CREATE TABLE IF NOT EXISTS workflow_triggers (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    event_source VARCHAR(100),
    event_type VARCHAR(100),
    conditions JSONB,
    schedule_pattern VARCHAR(100),
    cooldown_period INTEGER, -- in seconds
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_workflow_trigger_workflow FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(id),
    CONSTRAINT chk_workflow_trigger_type CHECK (
        trigger_type IN ('event', 'schedule', 'manual', 'api')
    )
);

CREATE TABLE IF NOT EXISTS workflow_conditions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    condition_type VARCHAR(50) NOT NULL,
    operator VARCHAR(20) NOT NULL,
    field_path VARCHAR(255),
    expected_value JSONB,
    custom_logic TEXT,
    error_message TEXT,
    sequence_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_workflow_condition_workflow FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(id),
    CONSTRAINT uq_workflow_condition_order UNIQUE (workflow_id, sequence_order),
    CONSTRAINT chk_workflow_condition_operator CHECK (
        operator IN ('equals', 'not_equals', 'greater_than', 'less_than', 'contains', 'not_contains', 'in', 'not_in', 'exists', 'not_exists')
    )
);

CREATE TABLE IF NOT EXISTS workflow_actions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    action_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_id VARCHAR(100),
    parameters JSONB,
    timeout INTEGER, -- in seconds
    retry_count INTEGER DEFAULT 0,
    sequence_order INTEGER NOT NULL,
    error_handling VARCHAR(20) DEFAULT 'stop',
    is_async BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_workflow_action_workflow FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(id),
    CONSTRAINT uq_workflow_action_order UNIQUE (workflow_id, sequence_order),
    CONSTRAINT chk_workflow_action_error CHECK (
        error_handling IN ('stop', 'continue', 'retry', 'skip')
    )
);

-- Level 4.59: Workflow Execution
CREATE TABLE IF NOT EXISTS workflow_schedules (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    schedule_type VARCHAR(50) NOT NULL,
    cron_expression VARCHAR(100),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    parameters JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_workflow_schedule_workflow FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(id),
    CONSTRAINT chk_workflow_schedule_dates CHECK (
        start_date <= end_date OR end_date IS NULL
    )
);

CREATE TABLE IF NOT EXISTS workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL,
    execution_id VARCHAR(50) NOT NULL UNIQUE,
    trigger_id INTEGER,
    schedule_id INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    input_data JSONB,
    output_data JSONB,
    error_details JSONB,
    current_action_id INTEGER,
    execution_path JSONB,
    duration INTEGER, -- in milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_workflow_execution_workflow FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(id),
    CONSTRAINT fk_workflow_execution_trigger FOREIGN KEY (trigger_id) REFERENCES workflow_triggers(id),
    CONSTRAINT fk_workflow_execution_schedule FOREIGN KEY (schedule_id) REFERENCES workflow_schedules(id),
    CONSTRAINT fk_workflow_execution_action FOREIGN KEY (current_action_id) REFERENCES workflow_actions(id),
    CONSTRAINT chk_workflow_execution_status CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'timeout')
    ),
    CONSTRAINT chk_workflow_execution_dates CHECK (
        started_at <= completed_at OR completed_at IS NULL
    )
);

-- Add indexes for better performance
CREATE INDEX idx_workflow_definitions_status ON workflow_definitions(status);
CREATE INDEX idx_workflow_definitions_category ON workflow_definitions(category);
CREATE INDEX idx_workflow_definitions_active ON workflow_definitions(is_active);

CREATE INDEX idx_workflow_triggers_workflow ON workflow_triggers(workflow_id);
CREATE INDEX idx_workflow_triggers_type ON workflow_triggers(trigger_type);
CREATE INDEX idx_workflow_triggers_event ON workflow_triggers(event_source, event_type);
CREATE INDEX idx_workflow_triggers_active ON workflow_triggers(is_active);

CREATE INDEX idx_workflow_conditions_workflow ON workflow_conditions(workflow_id);
CREATE INDEX idx_workflow_conditions_type ON workflow_conditions(condition_type);
CREATE INDEX idx_workflow_conditions_order ON workflow_conditions(sequence_order);

CREATE INDEX idx_workflow_actions_workflow ON workflow_actions(workflow_id);
CREATE INDEX idx_workflow_actions_type ON workflow_actions(action_type);
CREATE INDEX idx_workflow_actions_target ON workflow_actions(target_type, target_id);
CREATE INDEX idx_workflow_actions_order ON workflow_actions(sequence_order);

CREATE INDEX idx_workflow_schedules_workflow ON workflow_schedules(workflow_id);
CREATE INDEX idx_workflow_schedules_dates ON workflow_schedules(start_date, end_date);
CREATE INDEX idx_workflow_schedules_next_run ON workflow_schedules(next_run_at);
CREATE INDEX idx_workflow_schedules_active ON workflow_schedules(is_active);

CREATE INDEX idx_workflow_executions_workflow ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_trigger ON workflow_executions(trigger_id);
CREATE INDEX idx_workflow_executions_schedule ON workflow_executions(schedule_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_dates ON workflow_executions(started_at, completed_at);

-- Add comments for documentation
COMMENT ON TABLE workflow_definitions IS 'Workflow process definitions';
COMMENT ON TABLE workflow_triggers IS 'Workflow trigger configurations';
COMMENT ON TABLE workflow_conditions IS 'Workflow conditional logic';
COMMENT ON TABLE workflow_actions IS 'Workflow action steps';
COMMENT ON TABLE workflow_schedules IS 'Workflow scheduling configuration';
COMMENT ON TABLE workflow_executions IS 'Workflow execution history';

-- Add trigger for workflow execution tracking
CREATE OR REPLACE FUNCTION track_workflow_execution()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        -- Update duration when workflow completes
        IF NEW.completed_at IS NOT NULL AND OLD.completed_at IS NULL THEN
            NEW.duration := EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at)) * 1000;
        END IF;

        -- Update execution path
        IF NEW.current_action_id IS NOT NULL AND 
           (OLD.current_action_id IS NULL OR NEW.current_action_id != OLD.current_action_id) THEN
            NEW.execution_path := jsonb_set(
                COALESCE(OLD.execution_path, '[]'::jsonb),
                array[jsonb_array_length(COALESCE(OLD.execution_path, '[]'::jsonb))::text],
                jsonb_build_object(
                    'action_id', NEW.current_action_id,
                    'timestamp', CURRENT_TIMESTAMP,
                    'status', NEW.status
                )
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER track_workflow_execution
    BEFORE UPDATE ON workflow_executions
    FOR EACH ROW
    EXECUTE FUNCTION track_workflow_execution();

COMMIT;
