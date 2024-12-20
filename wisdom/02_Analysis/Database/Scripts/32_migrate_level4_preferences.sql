-- Migration Script - Level 4.16 (User Preferences and Settings)
-- Generated: 2024-12-19
-- Description: Creates user preferences, settings, and customization tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS widget_instances CASCADE;
DROP TABLE IF EXISTS dashboard_widgets CASCADE;
DROP TABLE IF EXISTS user_dashboards CASCADE;
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS preference_definitions CASCADE;

-- Level 4.46: Preference Configuration
CREATE TABLE IF NOT EXISTS preference_definitions (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    data_type VARCHAR(50) NOT NULL,
    default_value TEXT,
    possible_values JSONB,
    validation_rules JSONB,
    is_system_preference BOOLEAN DEFAULT false,
    is_user_configurable BOOLEAN DEFAULT true,
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_preference_definition_name UNIQUE (category, name)
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    preference_id INTEGER NOT NULL,
    preference_value TEXT NOT NULL,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_user_preference_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_user_preference_definition FOREIGN KEY (preference_id) REFERENCES preference_definitions(id),
    CONSTRAINT uq_user_preference UNIQUE (user_id, preference_id)
);

-- Level 4.47: Dashboard Configuration
CREATE TABLE IF NOT EXISTS user_dashboards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    layout_config JSONB,
    is_default BOOLEAN DEFAULT false,
    is_system_dashboard BOOLEAN DEFAULT false,
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_user_dashboard_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT uq_user_dashboard_name UNIQUE (user_id, name)
);

CREATE TABLE IF NOT EXISTS dashboard_widgets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    widget_type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    default_config JSONB,
    min_width INTEGER,
    min_height INTEGER,
    max_width INTEGER,
    max_height INTEGER,
    refresh_interval INTEGER, -- in seconds
    is_system_widget BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_dashboard_widget_name UNIQUE (name),
    CONSTRAINT chk_widget_dimensions CHECK (
        min_width > 0 AND min_height > 0 AND
        (max_width IS NULL OR max_width >= min_width) AND
        (max_height IS NULL OR max_height >= min_height)
    ),
    CONSTRAINT chk_widget_refresh CHECK (
        refresh_interval IS NULL OR refresh_interval > 0
    )
);

CREATE TABLE IF NOT EXISTS widget_instances (
    id SERIAL PRIMARY KEY,
    dashboard_id INTEGER NOT NULL,
    widget_id INTEGER NOT NULL,
    instance_name VARCHAR(100),
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    config JSONB,
    refresh_interval INTEGER, -- in seconds, overrides widget default
    is_minimized BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_widget_instance_dashboard FOREIGN KEY (dashboard_id) REFERENCES user_dashboards(id),
    CONSTRAINT fk_widget_instance_widget FOREIGN KEY (widget_id) REFERENCES dashboard_widgets(id),
    CONSTRAINT chk_widget_instance_position CHECK (
        position_x >= 0 AND position_y >= 0
    ),
    CONSTRAINT chk_widget_instance_size CHECK (
        width > 0 AND height > 0
    ),
    CONSTRAINT chk_widget_instance_refresh CHECK (
        refresh_interval IS NULL OR refresh_interval > 0
    )
);

-- Add indexes for better performance
CREATE INDEX idx_preference_definitions_category ON preference_definitions(category);
CREATE INDEX idx_preference_definitions_system ON preference_definitions(is_system_preference);
CREATE INDEX idx_preference_definitions_configurable ON preference_definitions(is_user_configurable);

CREATE INDEX idx_user_preferences_user ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_definition ON user_preferences(preference_id);
CREATE INDEX idx_user_preferences_default ON user_preferences(is_default);

CREATE INDEX idx_user_dashboards_user ON user_dashboards(user_id);
CREATE INDEX idx_user_dashboards_default ON user_dashboards(is_default);
CREATE INDEX idx_user_dashboards_system ON user_dashboards(is_system_dashboard);

CREATE INDEX idx_dashboard_widgets_type ON dashboard_widgets(widget_type);
CREATE INDEX idx_dashboard_widgets_category ON dashboard_widgets(category);
CREATE INDEX idx_dashboard_widgets_system ON dashboard_widgets(is_system_widget);
CREATE INDEX idx_dashboard_widgets_active ON dashboard_widgets(is_active);

CREATE INDEX idx_widget_instances_dashboard ON widget_instances(dashboard_id);
CREATE INDEX idx_widget_instances_widget ON widget_instances(widget_id);

-- Add comments for documentation
COMMENT ON TABLE preference_definitions IS 'System and user preference definitions';
COMMENT ON TABLE user_preferences IS 'User preference values';
COMMENT ON TABLE user_dashboards IS 'User dashboard configurations';
COMMENT ON TABLE dashboard_widgets IS 'Available dashboard widgets';
COMMENT ON TABLE widget_instances IS 'Dashboard widget instances';

-- Add trigger for widget instance dimension validation
CREATE OR REPLACE FUNCTION validate_widget_dimensions()
RETURNS TRIGGER AS $$
DECLARE
    min_w INTEGER;
    min_h INTEGER;
    max_w INTEGER;
    max_h INTEGER;
BEGIN
    SELECT min_width, min_height, max_width, max_height
    INTO min_w, min_h, max_w, max_h
    FROM dashboard_widgets
    WHERE id = NEW.widget_id;

    IF NEW.width < min_w OR (max_w IS NOT NULL AND NEW.width > max_w) THEN
        RAISE EXCEPTION 'Widget width must be between % and %', min_w, COALESCE(max_w, 'unlimited');
    END IF;

    IF NEW.height < min_h OR (max_h IS NOT NULL AND NEW.height > max_h) THEN
        RAISE EXCEPTION 'Widget height must be between % and %', min_h, COALESCE(max_h, 'unlimited');
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_widget_dimensions
    BEFORE INSERT OR UPDATE ON widget_instances
    FOR EACH ROW
    EXECUTE FUNCTION validate_widget_dimensions();

COMMIT;
