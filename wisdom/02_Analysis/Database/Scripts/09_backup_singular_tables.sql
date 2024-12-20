-- Backup Script for Singular Tables
-- Generated: 2024-12-19
-- Purpose: Create backup tables for singular versions before dropping them

BEGIN;

-- Create backup schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS backup_tables;

-- Create backup log table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.table_backup_log (
    id SERIAL PRIMARY KEY,
    original_schema VARCHAR(255),
    original_table VARCHAR(255),
    backup_schema VARCHAR(255),
    backup_table VARCHAR(255),
    backup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER,
    status VARCHAR(50),
    error_message TEXT
);

-- Function to safely backup a table
CREATE OR REPLACE FUNCTION backup_tables.backup_table(
    p_source_schema TEXT,
    p_source_table TEXT,
    p_backup_schema TEXT,
    p_backup_table TEXT
) RETURNS VOID AS $$
BEGIN
    -- Create backup table
    EXECUTE format(
        'CREATE TABLE %I.%I AS SELECT * FROM %I.%I',
        p_backup_schema,
        p_backup_table,
        p_source_schema,
        p_source_table
    );

    -- Log successful backup
    INSERT INTO public.table_backup_log (
        original_schema, 
        original_table, 
        backup_schema, 
        backup_table, 
        row_count,
        status
    )
    SELECT 
        p_source_schema,
        p_source_table,
        p_backup_schema,
        p_backup_table,
        (SELECT count(*) FROM public.audit_log),
        'SUCCESS';

EXCEPTION WHEN OTHERS THEN
    -- Log failed backup
    INSERT INTO public.table_backup_log (
        original_schema, 
        original_table, 
        backup_schema, 
        backup_table,
        status,
        error_message
    ) VALUES (
        p_source_schema,
        p_source_table,
        p_backup_schema,
        p_backup_table,
        'ERROR',
        SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- Backup each table individually
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
        BEGIN
            PERFORM backup_tables.backup_table(
                'public',
                v_table.table_name,
                'backup_tables',
                v_table.table_name || '_20241219'
            );
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Failed to backup table %: %', v_table.table_name, SQLERRM;
        END;
    END LOOP;
END $$;

-- Show backup results
SELECT 
    original_table,
    backup_table,
    status,
    row_count,
    error_message,
    backup_date
FROM public.table_backup_log
WHERE backup_date >= (current_timestamp - interval '5 minutes')
ORDER BY 
    CASE status
        WHEN 'ERROR' THEN 1
        ELSE 2
    END,
    original_table;

COMMIT;
