-- Enhanced Rename Script with Logging
-- Generated: 2024-12-16
-- Purpose: Rename tables with progress tracking and detailed logging

BEGIN;

-- Verify configuration exists
DO $$
DECLARE
    v_schema VARCHAR;
    v_prefix VARCHAR;
    v_batch_size INTEGER;
BEGIN
    -- Get settings
    SELECT setting_value INTO v_schema 
    FROM rename_config.settings 
    WHERE setting_key = 'target_schema';
    
    IF v_schema IS NULL THEN
        RAISE EXCEPTION 'Configuration not found. Please run 05_pre_rename_validation.sql first.';
    END IF;
    
    -- Verify no errors from validation
    IF EXISTS (
        SELECT 1 
        FROM public.table_rename_log 
        WHERE schema_name = v_schema 
        AND status = 'ERROR'
        AND created_at >= (current_timestamp - interval '5 minutes')
    ) THEN
        RAISE EXCEPTION 'Validation errors exist. Please fix them before proceeding.';
    END IF;
END $$;

-- Create progress tracking table
CREATE TEMP TABLE rename_progress (
    id SERIAL PRIMARY KEY,
    schema_name VARCHAR(255),
    old_name VARCHAR(255),
    new_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Insert planned changes
INSERT INTO rename_progress (schema_name, old_name, new_name)
SELECT 
    table_schema,
    table_name,
    regexp_replace(table_name, '^tbl_(.+)$', '\1')
FROM information_schema.tables 
WHERE table_schema = (
    SELECT setting_value 
    FROM rename_config.settings 
    WHERE setting_key = 'target_schema'
)
AND table_type = 'BASE TABLE'
AND table_name LIKE 'tbl_%';

-- Show planned changes
SELECT * FROM rename_progress ORDER BY id;

-- Perform renames
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT * FROM rename_progress WHERE status = 'pending' ORDER BY id
    LOOP
        BEGIN
            -- Update status
            UPDATE rename_progress 
            SET status = 'in_progress', 
                started_at = CURRENT_TIMESTAMP
            WHERE id = r.id;

            -- Perform rename
            EXECUTE format(
                'ALTER TABLE %I.%I RENAME TO %I',
                r.schema_name, r.old_name, r.new_name
            );

            -- Log success
            INSERT INTO public.table_rename_log (
                schema_name, old_name, new_name, 
                validation_type, message, status
            ) VALUES (
                r.schema_name, r.old_name, r.new_name,
                'rename', 'Successfully renamed', 'SUCCESS'
            );

            -- Update progress
            UPDATE rename_progress 
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP
            WHERE id = r.id;

        EXCEPTION WHEN OTHERS THEN
            -- Log error
            INSERT INTO public.table_rename_log (
                schema_name, old_name, new_name,
                validation_type, message, status
            ) VALUES (
                r.schema_name, r.old_name, r.new_name,
                'rename', SQLERRM, 'ERROR'
            );

            -- Update progress
            UPDATE rename_progress 
            SET status = 'error',
                error_message = SQLERRM,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = r.id;

            RAISE NOTICE 'Error renaming %: %', r.old_name, SQLERRM;
        END;
    END LOOP;
END $$;

-- Show results
SELECT 
    schema_name,
    old_name,
    new_name,
    status,
    started_at,
    completed_at,
    error_message
FROM rename_progress
ORDER BY id;

COMMIT;
