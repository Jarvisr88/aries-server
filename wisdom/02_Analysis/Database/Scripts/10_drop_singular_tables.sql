-- Drop Script for Singular Tables
-- Generated: 2024-12-19
-- Purpose: Drop singular version tables after backup

BEGIN;

-- Verify backups exist before dropping
DO $$
DECLARE
    missing_backup TEXT;
BEGIN
    SELECT string_agg(backup_table, ', ')
    INTO missing_backup
    FROM (
        SELECT t.table_name || '_20241216' as backup_table
        FROM (VALUES 
            ('audit_log'),
            ('customer'),
            ('customer_insurance'),
            ('doctor'),
            ('insurance_company'),
            ('maintenance_log'),
            ('maintenance_schedule'),
            ('payment'),
            ('warehouse')
        ) AS t(table_name)
        WHERE NOT EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = 'backup_tables' 
            AND table_name = t.table_name || '_20241216'
        )
    ) missing;

    IF missing_backup IS NOT NULL THEN
        RAISE EXCEPTION 'Missing backup tables: %', missing_backup;
    END IF;
END $$;

-- Function to safely drop a table
CREATE OR REPLACE FUNCTION public.drop_table_if_exists(
    p_schema text,
    p_table text
) RETURNS void AS $$
BEGIN
    -- Check if table exists
    IF EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = p_schema 
        AND table_name = p_table
    ) THEN
        -- Drop constraints first
        EXECUTE (
            SELECT string_agg(format('ALTER TABLE %I.%I DROP CONSTRAINT IF EXISTS %I CASCADE;', 
                p_schema, p_table, constraint_name), E'\n')
            FROM information_schema.table_constraints 
            WHERE table_schema = p_schema 
            AND table_name = p_table
        );
        
        -- Drop the table
        EXECUTE format('DROP TABLE IF EXISTS %I.%I CASCADE;', p_schema, p_table);
        
        -- Log success
        INSERT INTO public.table_rename_log (
            schema_name, 
            old_name, 
            new_name, 
            validation_type, 
            message, 
            status
        ) VALUES (
            p_schema,
            p_table,
            p_table || 's',
            'cleanup_duplicate',
            'Successfully dropped singular table',
            'SUCCESS'
        );
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- Log error
    INSERT INTO public.table_rename_log (
        schema_name, 
        old_name, 
        new_name, 
        validation_type, 
        message, 
        status
    ) VALUES (
        p_schema,
        p_table,
        p_table || 's',
        'cleanup_duplicate',
        'Error dropping table: ' || SQLERRM,
        'ERROR'
    );
END;
$$ LANGUAGE plpgsql;

-- Drop each table individually
DO $$
DECLARE
    v_table record;
BEGIN
    FOR v_table IN 
        SELECT table_name 
        FROM (VALUES 
            ('audit_log'),
            ('customer'),
            ('customer_insurance'),
            ('doctor'),
            ('insurance_company'),
            ('maintenance_log'),
            ('maintenance_schedule'),
            ('payment'),
            ('warehouse')
        ) AS t(table_name)
    LOOP
        PERFORM public.drop_table_if_exists('public', v_table.table_name);
    END LOOP;
END $$;

-- Show results
SELECT 
    old_name,
    new_name,
    status,
    message
FROM public.table_rename_log
WHERE validation_type = 'cleanup_duplicate'
AND created_at >= (current_timestamp - interval '5 minutes')
ORDER BY 
    CASE status
        WHEN 'ERROR' THEN 1
        ELSE 2
    END,
    old_name;

-- Cleanup
DROP FUNCTION IF EXISTS public.drop_table_if_exists;

COMMIT;
