-- Migration Script - Level 4.18 (Integration and API Management)
-- Generated: 2024-12-19
-- Description: Creates integration, API, and external system connection tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS api_metrics CASCADE;
DROP TABLE IF EXISTS api_logs CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS integration_mappings CASCADE;
DROP TABLE IF EXISTS integration_endpoints CASCADE;
DROP TABLE IF EXISTS integration_connections CASCADE;

-- Level 4.53: Integration Configuration
CREATE TABLE IF NOT EXISTS integration_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    connection_type VARCHAR(50) NOT NULL,
    credentials JSONB,
    settings JSONB,
    status VARCHAR(20) DEFAULT 'inactive',
    last_connected_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_integration_connection_name UNIQUE (name),
    CONSTRAINT chk_integration_connection_status CHECK (
        status IN ('active', 'inactive', 'error', 'rate_limited')
    )
);

CREATE TABLE IF NOT EXISTS integration_endpoints (
    id SERIAL PRIMARY KEY,
    connection_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    endpoint_type VARCHAR(50) NOT NULL,
    method VARCHAR(10),
    url_pattern VARCHAR(500),
    request_template JSONB,
    response_template JSONB,
    headers JSONB,
    timeout INTEGER, -- in seconds
    retry_policy JSONB,
    rate_limit INTEGER,
    rate_limit_period VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_integration_endpoint_connection FOREIGN KEY (connection_id) REFERENCES integration_connections(id),
    CONSTRAINT uq_integration_endpoint_name UNIQUE (connection_id, name),
    CONSTRAINT chk_integration_endpoint_method CHECK (
        method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH')
    )
);

-- Level 4.54: Data Mapping
CREATE TABLE IF NOT EXISTS integration_mappings (
    id SERIAL PRIMARY KEY,
    endpoint_id INTEGER NOT NULL,
    mapping_type VARCHAR(50) NOT NULL,
    source_model VARCHAR(100) NOT NULL,
    target_model VARCHAR(100) NOT NULL,
    field_mappings JSONB NOT NULL,
    transformation_rules JSONB,
    validation_rules JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_integration_mapping_endpoint FOREIGN KEY (endpoint_id) REFERENCES integration_endpoints(id),
    CONSTRAINT uq_integration_mapping UNIQUE (endpoint_id, mapping_type, source_model, target_model)
);

-- Level 4.55: API Security
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_identifier VARCHAR(100) NOT NULL UNIQUE,
    key_secret VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id INTEGER,
    permissions JSONB,
    rate_limit INTEGER,
    rate_limit_period VARCHAR(20),
    ip_whitelist TEXT[],
    valid_from TIMESTAMP NOT NULL,
    valid_until TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_api_key_owner FOREIGN KEY (owner_id) REFERENCES users(id),
    CONSTRAINT chk_api_key_dates CHECK (
        valid_from < valid_until OR valid_until IS NULL
    )
);

-- Level 4.56: API Monitoring
CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER,
    endpoint_id INTEGER,
    request_id VARCHAR(50) NOT NULL,
    request_method VARCHAR(10) NOT NULL,
    request_path VARCHAR(500) NOT NULL,
    request_headers JSONB,
    request_body JSONB,
    response_status INTEGER,
    response_headers JSONB,
    response_body JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    duration INTEGER, -- in milliseconds
    error_type VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_api_log_key FOREIGN KEY (api_key_id) REFERENCES api_keys(id),
    CONSTRAINT fk_api_log_endpoint FOREIGN KEY (endpoint_id) REFERENCES integration_endpoints(id)
);

CREATE TABLE IF NOT EXISTS api_metrics (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER,
    endpoint_id INTEGER,
    timestamp TIMESTAMP NOT NULL,
    requests_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    total_duration BIGINT DEFAULT 0, -- in milliseconds
    avg_duration INTEGER, -- in milliseconds
    min_duration INTEGER, -- in milliseconds
    max_duration INTEGER, -- in milliseconds
    status_codes JSONB, -- counts by status code
    error_types JSONB, -- counts by error type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_api_metric_key FOREIGN KEY (api_key_id) REFERENCES api_keys(id),
    CONSTRAINT fk_api_metric_endpoint FOREIGN KEY (endpoint_id) REFERENCES integration_endpoints(id)
);

-- Add indexes for better performance
CREATE INDEX idx_integration_connections_provider ON integration_connections(provider);
CREATE INDEX idx_integration_connections_type ON integration_connections(connection_type);
CREATE INDEX idx_integration_connections_status ON integration_connections(status);
CREATE INDEX idx_integration_connections_active ON integration_connections(is_active);

CREATE INDEX idx_integration_endpoints_connection ON integration_endpoints(connection_id);
CREATE INDEX idx_integration_endpoints_type ON integration_endpoints(endpoint_type);
CREATE INDEX idx_integration_endpoints_method ON integration_endpoints(method);
CREATE INDEX idx_integration_endpoints_active ON integration_endpoints(is_active);

CREATE INDEX idx_integration_mappings_endpoint ON integration_mappings(endpoint_id);
CREATE INDEX idx_integration_mappings_type ON integration_mappings(mapping_type);
CREATE INDEX idx_integration_mappings_models ON integration_mappings(source_model, target_model);
CREATE INDEX idx_integration_mappings_active ON integration_mappings(is_active);

CREATE INDEX idx_api_keys_identifier ON api_keys(key_identifier);
CREATE INDEX idx_api_keys_owner ON api_keys(owner_id);
CREATE INDEX idx_api_keys_dates ON api_keys(valid_from, valid_until);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);

CREATE INDEX idx_api_logs_key ON api_logs(api_key_id);
CREATE INDEX idx_api_logs_endpoint ON api_logs(endpoint_id);
CREATE INDEX idx_api_logs_request ON api_logs(request_id);
CREATE INDEX idx_api_logs_date ON api_logs(created_at);
CREATE INDEX idx_api_logs_status ON api_logs(response_status);

CREATE INDEX idx_api_metrics_key ON api_metrics(api_key_id);
CREATE INDEX idx_api_metrics_endpoint ON api_metrics(endpoint_id);
CREATE INDEX idx_api_metrics_timestamp ON api_metrics(timestamp);

-- Add comments for documentation
COMMENT ON TABLE integration_connections IS 'External system connection configurations';
COMMENT ON TABLE integration_endpoints IS 'Integration endpoint definitions';
COMMENT ON TABLE integration_mappings IS 'Data mapping configurations';
COMMENT ON TABLE api_keys IS 'API key management';
COMMENT ON TABLE api_logs IS 'API request/response logs';
COMMENT ON TABLE api_metrics IS 'API usage metrics';

-- Add trigger for API metrics aggregation
CREATE OR REPLACE FUNCTION aggregate_api_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert metrics
    INSERT INTO api_metrics (
        api_key_id,
        endpoint_id,
        timestamp,
        requests_count,
        success_count,
        error_count,
        total_duration,
        avg_duration,
        min_duration,
        max_duration,
        status_codes,
        error_types
    )
    VALUES (
        NEW.api_key_id,
        NEW.endpoint_id,
        date_trunc('hour', NEW.created_at),
        1,
        CASE WHEN NEW.response_status < 400 THEN 1 ELSE 0 END,
        CASE WHEN NEW.response_status >= 400 THEN 1 ELSE 0 END,
        NEW.duration,
        NEW.duration,
        NEW.duration,
        NEW.duration,
        jsonb_build_object(NEW.response_status::text, 1),
        CASE 
            WHEN NEW.error_type IS NOT NULL 
            THEN jsonb_build_object(NEW.error_type, 1)
            ELSE '{}'::jsonb
        END
    )
    ON CONFLICT (api_key_id, endpoint_id, timestamp) DO UPDATE
    SET
        requests_count = api_metrics.requests_count + 1,
        success_count = api_metrics.success_count + CASE WHEN NEW.response_status < 400 THEN 1 ELSE 0 END,
        error_count = api_metrics.error_count + CASE WHEN NEW.response_status >= 400 THEN 1 ELSE 0 END,
        total_duration = api_metrics.total_duration + NEW.duration,
        avg_duration = (api_metrics.total_duration + NEW.duration) / (api_metrics.requests_count + 1),
        min_duration = LEAST(api_metrics.min_duration, NEW.duration),
        max_duration = GREATEST(api_metrics.max_duration, NEW.duration),
        status_codes = api_metrics.status_codes || 
            jsonb_build_object(
                NEW.response_status::text,
                COALESCE((api_metrics.status_codes->>NEW.response_status::text)::integer, 0) + 1
            ),
        error_types = CASE 
            WHEN NEW.error_type IS NOT NULL THEN
                api_metrics.error_types || 
                jsonb_build_object(
                    NEW.error_type,
                    COALESCE((api_metrics.error_types->>NEW.error_type)::integer, 0) + 1
                )
            ELSE api_metrics.error_types
        END;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER aggregate_api_metrics
    AFTER INSERT ON api_logs
    FOR EACH ROW
    EXECUTE FUNCTION aggregate_api_metrics();

COMMIT;
