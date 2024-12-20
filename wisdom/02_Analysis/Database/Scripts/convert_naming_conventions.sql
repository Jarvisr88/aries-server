-- Convert Naming Conventions Script
-- Version: 2024-12-16
-- Description: Converts table names from source to target naming convention
-- Author: Cascade AI

-- Drop existing functions
DROP FUNCTION IF EXISTS convert_table_name(text);
DROP FUNCTION IF EXISTS preview_name_changes();
DROP FUNCTION IF EXISTS execute_name_conversion();

-- Function to convert table name from source to target convention
CREATE OR REPLACE FUNCTION convert_table_name(source_name text)
RETURNS text AS $$
DECLARE
    target_name text;
BEGIN
    -- Remove 'tbl_' prefix if it exists
    target_name := regexp_replace(source_name, '^tbl_', '');
    
    -- Convert to snake_case
    target_name := lower(regexp_replace(target_name, '([A-Z])', '_\1', 'g'));
    target_name := regexp_replace(target_name, '^_', ''); -- Remove leading underscore
    
    -- Convert to plural form if not already plural
    IF NOT (target_name LIKE '%s' OR target_name LIKE '%es') THEN
        -- Handle special cases first
        target_name := CASE
            WHEN target_name LIKE '%y' AND NOT (target_name LIKE '%[aeiou]y') THEN 
                regexp_replace(target_name, 'y$', 'ies')
            WHEN target_name LIKE '%s' OR target_name LIKE '%x' OR target_name LIKE '%ch' OR target_name LIKE '%sh' THEN 
                target_name || 'es'
            ELSE 
                target_name || 's'
        END;
    END IF;
    
    RETURN target_name;
END;
$$ LANGUAGE plpgsql;

-- Create conversion log table if not exists
CREATE TABLE IF NOT EXISTS public.naming_convention_log (
    id serial PRIMARY KEY,
    schema_name text NOT NULL,
    old_name text NOT NULL,
    new_name text NOT NULL,
    converted_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status text NOT NULL
);

-- Function to preview changes
CREATE OR REPLACE FUNCTION preview_name_changes()
RETURNS TABLE(schema_name text, old_name text, new_name text) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.table_schema,
        t.table_name,
        convert_table_name(t.table_name)
    FROM information_schema.tables t
    WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
    AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_schema, t.table_name;
END;
$$ LANGUAGE plpgsql;

-- Function to execute rename with logging
CREATE OR REPLACE FUNCTION execute_name_conversion()
RETURNS SETOF text AS $$
DECLARE
    tbl record;
    result_message text;
BEGIN
    FOR tbl IN 
        SELECT 
            table_schema,
            table_name,
            convert_table_name(table_name) as new_name
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_type = 'BASE TABLE'
    LOOP
        BEGIN
            -- Execute rename
            EXECUTE format(
                'ALTER TABLE %I.%I RENAME TO %I',
                tbl.table_schema,
                tbl.table_name,
                tbl.new_name
            );
            
            -- Log success
            INSERT INTO public.naming_convention_log 
                (schema_name, old_name, new_name, status)
            VALUES 
                (tbl.table_schema, tbl.table_name, tbl.new_name, 'SUCCESS');
            
            result_message := format('Renamed %.% to %.%', 
                tbl.table_schema, tbl.table_name,
                tbl.table_schema, tbl.new_name);
            RAISE NOTICE '%', result_message;
            RETURN NEXT result_message;
            
        EXCEPTION WHEN OTHERS THEN
            -- Log failure
            INSERT INTO public.naming_convention_log 
                (schema_name, old_name, new_name, status)
            VALUES 
                (tbl.table_schema, tbl.table_name, tbl.new_name, 'FAILED: ' || SQLERRM);
            
            result_message := format('Failed to rename %.%: %', 
                tbl.table_schema, tbl.table_name, SQLERRM);
            RAISE NOTICE '%', result_message;
            RETURN NEXT result_message;
        END;
    END LOOP;
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- First, drop the extra logging table
DROP TABLE IF EXISTS public.naming_convention_log;

-- Function to properly pluralize table names
CREATE OR REPLACE FUNCTION proper_plural(singular text)
RETURNS text AS $$
BEGIN
    -- If already plural, return as is
    IF singular LIKE '%s' OR singular LIKE '%es' THEN
        RETURN singular;
    END IF;

    -- Special cases for irregular plurals
    IF singular LIKE '%y' AND NOT singular ~ '[aeiou]y$' THEN
        RETURN regexp_replace(singular, 'y$', 'ies');
    END IF;

    -- Words ending in 'company'
    IF singular LIKE '%company' THEN
        RETURN regexp_replace(singular, 'company$', 'companies');
    END IF;

    -- Words ending in 'category'
    IF singular LIKE '%category' THEN
        RETURN regexp_replace(singular, 'category$', 'categories');
    END IF;

    -- Add 'es' to words ending in 's', 'sh', 'ch', 'x', 'z'
    IF singular ~ '(s|sh|ch|x|z)$' THEN
        RETURN singular || 'es';
    END IF;

    -- Default case: just add 's'
    RETURN singular || 's';
END;
$$ LANGUAGE plpgsql;

-- Create temporary table to store results
CREATE TEMP TABLE conversion_results AS
WITH table_info AS (
    SELECT 
        t.table_schema,
        t.table_name,
        CASE 
            WHEN t.table_name LIKE 'tbl_%' THEN 
                proper_plural(regexp_replace(lower(t.table_name), '^tbl_(.+)$', '\1'))
            ELSE 
                CASE 
                    WHEN t.table_name ~ 's$' THEN lower(t.table_name)  -- already plural
                    ELSE proper_plural(lower(t.table_name))
                END
        END as new_name,
        (SELECT COUNT(*) 
         FROM information_schema.columns c 
         WHERE c.table_schema = t.table_schema 
         AND c.table_name = t.table_name) as column_count,
        (SELECT string_agg(column_name || ' ' || data_type, ', ' ORDER BY ordinal_position)
         FROM information_schema.columns c 
         WHERE c.table_schema = t.table_schema 
         AND c.table_name = t.table_name) as columns_list,
        obj_description(
            (quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))::regclass, 
            'pg_class'
        ) as table_description,
        (SELECT COUNT(*) 
         FROM information_schema.table_constraints tc 
         WHERE tc.table_schema = t.table_schema 
         AND tc.table_name = t.table_name 
         AND tc.constraint_type = 'PRIMARY KEY') as has_primary_key,
        (SELECT COUNT(*) 
         FROM information_schema.table_constraints tc 
         WHERE tc.table_schema = t.table_schema 
         AND tc.table_name = t.table_name 
         AND tc.constraint_type = 'FOREIGN KEY') as foreign_key_count
    FROM information_schema.tables t
    WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
    AND t.table_type = 'BASE TABLE'
)
SELECT 
    table_schema,
    table_name,
    new_name,
    column_count,
    columns_list,
    COALESCE(table_description, 'No description available') as description,
    has_primary_key,
    foreign_key_count
FROM table_info
ORDER BY table_schema, table_name;

-- Export results to JSON
COPY (
    SELECT json_agg(json_build_object(
        'schema', table_schema,
        'current_name', table_name,
        'new_name', new_name,
        'structure', json_build_object(
            'column_count', column_count,
            'columns', columns_list,
            'has_primary_key', has_primary_key > 0,
            'foreign_key_count', foreign_key_count
        ),
        'description', description,
        'rename_sql', format('ALTER TABLE %I.%I RENAME TO %I;', 
                           table_schema, table_name, new_name),
        'needs_rename', CASE 
            WHEN lower(table_name) != new_name THEN true 
            ELSE false 
        END,
        'changes', json_build_object(
            'removes_tbl_prefix', table_name LIKE 'tbl_%',
            'converts_to_plural', NOT (table_name ~ 's$'),
            'changes_case', table_name != lower(table_name)
        ),
        'validation', json_build_object(
            'has_primary_key', has_primary_key > 0,
            'has_foreign_keys', foreign_key_count > 0,
            'column_count_ok', column_count > 0
        )
    ))
    FROM conversion_results
) TO 'A:\Aries Enterprise\wisdom\02_Analysis\Database\Scripts\convert_4_results.json';

-- Show detailed summary
SELECT 
    table_schema as schema,
    COUNT(*) as total_tables,
    SUM(CASE WHEN lower(table_name) != new_name THEN 1 ELSE 0 END) as tables_to_rename,
    SUM(CASE WHEN table_name LIKE 'tbl_%' THEN 1 ELSE 0 END) as tbl_prefix_count,
    SUM(CASE WHEN NOT (table_name ~ 's$') THEN 1 ELSE 0 END) as non_plural_count,
    SUM(CASE WHEN table_name != lower(table_name) THEN 1 ELSE 0 END) as case_changes_needed,
    SUM(CASE WHEN has_primary_key = 0 THEN 1 ELSE 0 END) as tables_without_pk,
    SUM(CASE WHEN foreign_key_count > 0 THEN 1 ELSE 0 END) as tables_with_fk,
    AVG(column_count)::numeric(10,2) as avg_columns_per_table
FROM conversion_results
GROUP BY table_schema
ORDER BY table_schema;

-- Show current tables and their counts by schema
SELECT 
    table_schema,
    COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
AND table_type = 'BASE TABLE'
GROUP BY table_schema
ORDER BY table_schema;
