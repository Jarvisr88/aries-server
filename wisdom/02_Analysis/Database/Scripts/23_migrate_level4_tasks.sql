-- Migration Script - Level 4.7 (Tasks and Workflow Management)
-- Generated: 2024-12-19
-- Description: Creates task management, workflow, and assignment tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS task_time_entries CASCADE;
DROP TABLE IF EXISTS task_comments CASCADE;
DROP TABLE IF EXISTS task_dependencies CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS task_types CASCADE;

-- Level 4.19: Task Management
CREATE TABLE IF NOT EXISTS task_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    default_priority INTEGER DEFAULT 0,
    estimated_duration INTEGER, -- in minutes
    requires_approval BOOLEAN DEFAULT false,
    is_system_type BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_task_type_name UNIQUE (name),
    CONSTRAINT chk_task_type_priority CHECK (default_priority >= 0),
    CONSTRAINT chk_task_type_duration CHECK (estimated_duration > 0 OR estimated_duration IS NULL)
);

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    task_type_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    due_date TIMESTAMP,
    start_date TIMESTAMP,
    completion_date TIMESTAMP,
    assigned_to INTEGER,
    assigned_by INTEGER,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    parent_task_id INTEGER,
    progress INTEGER DEFAULT 0,
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_task_type FOREIGN KEY (task_type_id) REFERENCES task_types(id),
    CONSTRAINT fk_task_assigned_to FOREIGN KEY (assigned_to) REFERENCES users(id),
    CONSTRAINT fk_task_assigned_by FOREIGN KEY (assigned_by) REFERENCES users(id),
    CONSTRAINT fk_task_parent FOREIGN KEY (parent_task_id) REFERENCES tasks(id),
    CONSTRAINT chk_task_priority CHECK (priority >= 0),
    CONSTRAINT chk_task_progress CHECK (progress >= 0 AND progress <= 100),
    CONSTRAINT chk_task_hours CHECK (
        estimated_hours >= 0 AND
        (actual_hours >= 0 OR actual_hours IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS task_dependencies (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,
    dependent_task_id INTEGER NOT NULL,
    dependency_type VARCHAR(20) DEFAULT 'finish_to_start',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_task_dependency_task FOREIGN KEY (task_id) REFERENCES tasks(id),
    CONSTRAINT fk_task_dependency_dependent FOREIGN KEY (dependent_task_id) REFERENCES tasks(id),
    CONSTRAINT chk_task_dependency_type CHECK (
        dependency_type IN ('finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish')
    )
);

-- Level 4.20: Task Comments and Time Tracking
CREATE TABLE IF NOT EXISTS task_comments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT false,
    parent_comment_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_task_comment_task FOREIGN KEY (task_id) REFERENCES tasks(id),
    CONSTRAINT fk_task_comment_parent FOREIGN KEY (parent_comment_id) REFERENCES task_comments(id)
);

CREATE TABLE IF NOT EXISTS task_time_entries (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration INTEGER, -- in minutes
    description TEXT,
    is_billable BOOLEAN DEFAULT true,
    billing_rate DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_task_time_task FOREIGN KEY (task_id) REFERENCES tasks(id),
    CONSTRAINT fk_task_time_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_task_time_duration CHECK (
        (end_time IS NULL AND duration IS NULL) OR
        (end_time IS NOT NULL AND duration > 0)
    )
);

-- Add indexes for better performance
CREATE INDEX idx_task_types_category ON task_types(category);
CREATE INDEX idx_task_types_name ON task_types(name);

CREATE INDEX idx_tasks_type ON tasks(task_type_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX idx_tasks_dates ON tasks(due_date, start_date, completion_date);
CREATE INDEX idx_tasks_entity ON tasks(entity_type, entity_id);
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id);

CREATE INDEX idx_task_dependencies_task ON task_dependencies(task_id);
CREATE INDEX idx_task_dependencies_dependent ON task_dependencies(dependent_task_id);
CREATE INDEX idx_task_dependencies_type ON task_dependencies(dependency_type);

CREATE INDEX idx_task_comments_task ON task_comments(task_id);
CREATE INDEX idx_task_comments_parent ON task_comments(parent_comment_id);

CREATE INDEX idx_task_time_entries_task ON task_time_entries(task_id);
CREATE INDEX idx_task_time_entries_user ON task_time_entries(user_id);
CREATE INDEX idx_task_time_entries_dates ON task_time_entries(start_time, end_time);

-- Add comments for documentation
COMMENT ON TABLE task_types IS 'Predefined types of tasks with default settings';
COMMENT ON TABLE tasks IS 'Main task tracking table';
COMMENT ON TABLE task_dependencies IS 'Dependencies between tasks';
COMMENT ON TABLE task_comments IS 'Comments and discussions on tasks';
COMMENT ON TABLE task_time_entries IS 'Time tracking for tasks';

-- Add trigger for task completion
CREATE OR REPLACE FUNCTION update_task_completion()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        NEW.completion_date = CURRENT_TIMESTAMP;
    END IF;
    IF NEW.status != 'completed' AND OLD.status = 'completed' THEN
        NEW.completion_date = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_task_completion_timestamp
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_task_completion();

COMMIT;
