-- Convert Naming Conventions Script
-- Version: 2024-12-16_10-41
-- Description: Converts table names from source to target naming convention
-- Author: Cascade AI
-- Connection: postgres@localhost:5432/aries_enterprise_dev

-- Function to convert table name from source to target convention
CREATE OR REPLACE FUNCTION convert_table_name(source_name text)
RETURNS text AS $$
DECLARE
    target_name text;
BEGIN
    -- Remove 'tbl_' prefix
    target_name := regexp_replace(source_name, '^tbl_', '');
    
    -- Convert to plural form
    -- Add basic pluralization rules
    target_name := CASE
        WHEN target_name LIKE '%y' THEN 
            regexp_replace(target_name, 'y$', 'ies')
        WHEN target_name LIKE '%s' OR target_name LIKE '%x' OR target_name LIKE '%ch' THEN 
            target_name || 'es'
        ELSE 
            target_name || 's'
    END;
    
    -- Convert to lowercase
    target_name := lower(target_name);
    
    RETURN target_name;
END;
$$ LANGUAGE plpgsql;

-- Function to generate rename statements
CREATE OR REPLACE FUNCTION generate_rename_statements()
RETURNS TABLE(rename_sql text) AS $$
DECLARE
    tbl record;
BEGIN
    FOR tbl IN 
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema IN ('c01', 'dmeworks', 'repository')
        AND table_type = 'BASE TABLE'
    LOOP
        rename_sql := format(
            'ALTER TABLE %I.%I RENAME TO %I;',
            tbl.table_schema,
            tbl.table_name,
            convert_table_name(tbl.table_name)
        );
        RETURN NEXT;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create conversion log table
CREATE TABLE IF NOT EXISTS public.naming_convention_log (
    id serial PRIMARY KEY,
    old_name text NOT NULL,
    new_name text NOT NULL,
    converted_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status text NOT NULL
);

-- Function to execute rename with logging
CREATE OR REPLACE FUNCTION execute_rename_with_logging()
RETURNS void AS $$
DECLARE
    rename_stmt text;
BEGIN
    FOR rename_stmt IN SELECT * FROM generate_rename_statements() LOOP
        BEGIN
            -- Extract old and new names for logging
            DECLARE
                old_name text := split_part(split_part(rename_stmt, 'RENAME TO', 1), '.', 2);
                new_name text := split_part(rename_stmt, 'RENAME TO', 2);
            BEGIN
                -- Execute rename
                EXECUTE rename_stmt;
                
                -- Log success
                INSERT INTO public.naming_convention_log (old_name, new_name, status)
                VALUES (trim(old_name), trim(new_name), 'SUCCESS');
                
                RAISE NOTICE 'Renamed table % to %', old_name, new_name;
            EXCEPTION WHEN OTHERS THEN
                -- Log failure
                INSERT INTO public.naming_convention_log (old_name, new_name, status)
                VALUES (trim(old_name), trim(new_name), 'FAILED: ' || SQLERRM);
                
                RAISE NOTICE 'Failed to rename % to %: %', old_name, new_name, SQLERRM;
            END;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT * FROM generate_rename_statements();  -- Preview changes
-- SELECT execute_rename_with_logging();        -- Execute changes
