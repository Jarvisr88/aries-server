-- Pluralization Validation Script
-- Generated: 2024-12-16
-- Purpose: Validate tables before pluralization to ensure safety and identify potential issues

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

-- Drop and recreate settings table
DROP TABLE IF EXISTS rename_config.settings;
CREATE TABLE rename_config.settings (
    setting_key VARCHAR(50) PRIMARY KEY,
    setting_value VARCHAR(255)
);

-- Insert fresh settings
INSERT INTO rename_config.settings (setting_key, setting_value)
VALUES 
    ('target_schema', 'public'),
    ('phase', 'pluralize'),
    ('batch_size', '50'),
    ('log_retention_days', '30');

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

-- Get list of tables to be pluralized
WITH table_analysis AS (
    SELECT 
        t.table_schema,
        t.table_name as current_name,
        CASE
            -- Handle -y to -ies (but not if vowel before y)
            WHEN t.table_name ~ '.*[^aeiou]y$' THEN 
                regexp_replace(t.table_name, 'y$', 'ies')
            -- Handle regular cases needing -s
            WHEN NOT t.table_name ~ '.*s$' THEN 
                t.table_name || 's'
            ELSE t.table_name -- Already plural
        END as suggested_name,
        CASE
            WHEN t.table_name ~ '.*s$' THEN 'Already plural'
            WHEN t.table_name ~ '.*[^aeiou]y$' THEN 'Needs -y to -ies'
            ELSE 'Needs -s'
        END as status
    FROM information_schema.tables t
    WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
    AND t.table_name NOT IN ('table_rename_log')  -- Exclude our logging table
    AND NOT t.table_name ~ '.*s$'  -- Exclude already plural tables
)
INSERT INTO public.table_rename_log (
    schema_name, old_name, new_name, validation_type, message, status
)
SELECT 
    table_schema,
    current_name,
    suggested_name,
    'pluralization_check',
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = ta.table_schema 
            AND table_name = ta.suggested_name
            AND table_name != ta.current_name
        ) THEN 'Target plural name already exists'
        ELSE 'Ready for pluralization: ' || current_name || ' -> ' || suggested_name
    END,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = ta.table_schema 
            AND table_name = ta.suggested_name
            AND table_name != ta.current_name
        ) THEN 'ERROR'
        ELSE 'READY'
    END
FROM table_analysis ta;

-- Show validation results with suggested changes
SELECT 
    schema_name,
    old_name as current_name,
    new_name as suggested_name,
    message,
    status,
    created_at
FROM public.table_rename_log
WHERE validation_type = 'pluralization_check'
AND created_at >= (current_timestamp - interval '5 minutes')
ORDER BY 
    CASE status
        WHEN 'ERROR' THEN 1
        WHEN 'READY' THEN 2
        ELSE 3
    END,
    current_name;

COMMIT;
