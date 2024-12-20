-- Pre-rename Validation Script
-- Generated: 2024-12-16
-- Purpose: Validate tables before renaming to ensure safety and identify potential issues

BEGIN;

-- Configuration Section
DO $$
BEGIN
    -- Create rename_config schema if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_namespace WHERE nspname = 'rename_config'
    ) THEN
        CREATE SCHEMA rename_config;
    END IF;
END $$;

-- Create settings table
CREATE TABLE IF NOT EXISTS rename_config.settings (
    setting_key VARCHAR(50) PRIMARY KEY,
    setting_value VARCHAR(255)
);

-- Create or update settings (single transaction)
INSERT INTO rename_config.settings (setting_key, setting_value)
VALUES 
    ('target_schema', 'public'),  -- Changed to public schema
    ('prefix_to_remove', 'tbl_'),
    ('batch_size', '50'),
    ('log_retention_days', '30')
ON CONFLICT (setting_key) 
DO UPDATE SET setting_value = EXCLUDED.setting_value;

-- Create log table if needed
CREATE TABLE IF NOT EXISTS public.table_rename_log (
    id SERIAL PRIMARY KEY,
    schema_name VARCHAR(255),
    old_name VARCHAR(255),
    new_name VARCHAR(255),
    validation_type VARCHAR(50),
    message TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Get configuration values
DO $$
DECLARE
    v_schema VARCHAR;
    v_prefix VARCHAR;
BEGIN
    SELECT setting_value INTO v_schema 
    FROM rename_config.settings 
    WHERE setting_key = 'target_schema';

    -- Validate schema exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.schemata 
        WHERE schema_name = v_schema
    ) THEN
        RAISE EXCEPTION 'Schema % does not exist', v_schema;
    END IF;

    -- Log validation start
    INSERT INTO public.table_rename_log 
    (schema_name, validation_type, message, status)
    VALUES 
    (v_schema, 'validation_start', 'Starting validation for schema: ' || v_schema, 'INFO');
END $$;

-- Perform validations in a single transaction
WITH target_tables AS (
    SELECT 
        t.table_schema,
        t.table_name as old_name,
        regexp_replace(t.table_name, '^tbl_(.+)$', '\1') as new_name
    FROM information_schema.tables t
    WHERE t.table_schema = (
        SELECT setting_value 
        FROM rename_config.settings 
        WHERE setting_key = 'target_schema'
    )
    AND t.table_type = 'BASE TABLE'
    AND t.table_name LIKE 'tbl_%'
)
INSERT INTO public.table_rename_log (
    schema_name, old_name, new_name, validation_type, message, status
)
SELECT 
    t.table_schema,
    t.old_name,
    t.new_name,
    'pre_validation',
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = t.table_schema 
            AND table_name = t.new_name
        ) THEN 'Target name already exists: ' || t.new_name
        ELSE 'Table ready for rename'
    END,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = t.table_schema 
            AND table_name = t.new_name
        ) THEN 'ERROR'
        ELSE 'READY'
    END
FROM target_tables t;

-- Show validation results
SELECT 
    schema_name,
    old_name,
    new_name,
    validation_type,
    message,
    status,
    created_at
FROM public.table_rename_log
WHERE created_at >= (current_timestamp - interval '5 minutes')
ORDER BY 
    CASE status
        WHEN 'ERROR' THEN 1
        WHEN 'WARNING' THEN 2
        ELSE 3
    END,
    created_at DESC;

COMMIT;
