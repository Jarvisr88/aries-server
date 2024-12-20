-- First, create the dblink extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS dblink;

-- First, test connection to source database (c01)
DO $$
BEGIN
    PERFORM dblink_connect('source_conn', 'host=localhost port=5432 dbname=c01 user=postgres password=Major8859!');
    RAISE NOTICE 'Successfully connected to c01 database';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Failed to connect to c01: %', SQLERRM;
END $$;

-- Test query on source database
SELECT 'Source Database Tables:' as debug_step;
SELECT * FROM dblink(
    'source_conn',
    'SELECT current_database() as db, count(*) as table_count 
     FROM pg_catalog.pg_tables 
     WHERE schemaname NOT IN (''pg_catalog'', ''information_schema'')'
) AS t(database text, table_count bigint);

-- Show current database name and tables
SELECT 'Current Database Info:' as debug_step;
SELECT current_database() as current_db;
SELECT schemaname, count(*) as table_count 
FROM pg_catalog.pg_tables 
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
GROUP BY schemaname;

-- Debug: Check source tables
SELECT 'Source Tables:' as debug_step;
SELECT * FROM dblink(
    'source_conn',
    'SELECT n.nspname, c.relname 
     FROM pg_catalog.pg_class c
     JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
     WHERE c.relkind = ''r''
     AND n.nspname NOT IN (''pg_catalog'', ''information_schema'')
     AND n.nspname NOT LIKE ''pg_temp%''
     AND n.nspname NOT LIKE ''pg_toast%''')
AS source(nspname text, relname text);

-- Debug: Check target tables
SELECT 'Target Tables:' as debug_step;
SELECT schemaname, tablename 
FROM pg_catalog.pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
AND schemaname NOT LIKE 'pg_temp%'
AND schemaname NOT LIKE 'pg_toast%';

-- Create a temporary table to store the results
DROP TABLE IF EXISTS temp_comparison_results;
CREATE TEMPORARY TABLE temp_comparison_results (
    schema_name text,
    table_name text,
    column_count integer,
    description text,
    create_statement text
);

-- Insert results into temporary table
WITH source_tables AS (
    SELECT 
        nspname as schema_name,
        relname as table_name
    FROM dblink(
        'source_conn',
        'SELECT n.nspname, c.relname 
         FROM pg_catalog.pg_class c
         JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
         WHERE c.relkind = ''r''
         AND n.nspname NOT IN (''pg_catalog'', ''information_schema'')
         AND n.nspname NOT LIKE ''pg_temp%''
         AND n.nspname NOT LIKE ''pg_toast%''')
    AS source(nspname text, relname text)
),
target_tables AS (
    SELECT 
        schemaname as schema_name,
        tablename as table_name
    FROM pg_catalog.pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    AND schemaname NOT LIKE 'pg_temp%'
    AND schemaname NOT LIKE 'pg_toast%'
),
missing_tables AS (
    SELECT 
        s.schema_name,
        s.table_name
    FROM source_tables s
    LEFT JOIN target_tables t ON 
        s.schema_name = t.schema_name 
        AND s.table_name = t.table_name
    WHERE t.table_name IS NULL
    ORDER BY s.schema_name, s.table_name
)
INSERT INTO temp_comparison_results
SELECT 
    m.schema_name,
    m.table_name,
    table_details.column_count,
    COALESCE(table_details.table_comment, 'No comment') as description,
    table_details.create_statement
FROM missing_tables m
CROSS JOIN LATERAL (
    SELECT *
    FROM dblink(
        'source_conn',
        format(
            'WITH table_info AS (
                SELECT 
                    c.oid,
                    (SELECT COUNT(*) 
                     FROM pg_catalog.pg_attribute a 
                     WHERE a.attrelid = c.oid 
                     AND a.attnum > 0 
                     AND NOT a.attisdropped) as column_count,
                    pg_catalog.obj_description(c.oid, ''pg_class'') as table_comment,
                    (
                        SELECT string_agg(
                            format(
                                ''    %%I %%s%%s%%s'',
                                a.attname,
                                pg_catalog.format_type(a.atttypid, a.atttypmod),
                                CASE WHEN a.attnotnull THEN '' NOT NULL'' ELSE '''' END,
                                CASE 
                                    WHEN pc.contype = ''p'' THEN '' PRIMARY KEY''
                                    WHEN pc.contype = ''f'' THEN format(
                                        '' REFERENCES %%I.%%I(%%I)'',
                                        ref_ns.nspname,
                                        ref_class.relname,
                                        ref_att.attname
                                    )
                                    ELSE ''''
                                END
                            ),
                            '','' ORDER BY a.attnum
                        )
                        FROM pg_catalog.pg_attribute a
                        LEFT JOIN pg_catalog.pg_constraint pc 
                            ON pc.conrelid = c.oid 
                            AND a.attnum = ANY(pc.conkey)
                        LEFT JOIN pg_catalog.pg_class ref_class 
                            ON pc.confrelid = ref_class.oid
                        LEFT JOIN pg_catalog.pg_namespace ref_ns 
                            ON ref_class.relnamespace = ref_ns.oid
                        LEFT JOIN pg_catalog.pg_attribute ref_att 
                            ON ref_att.attrelid = pc.confrelid
                            AND ref_att.attnum = pc.confkey[array_position(pc.conkey, a.attnum)]
                        WHERE a.attrelid = c.oid 
                        AND a.attnum > 0 
                        AND NOT a.attisdropped
                    ) as columns_def
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = %L
                AND n.nspname = %L
            )
            SELECT 
                column_count,
                table_comment,
                format(
                    E''-- Table: %%I.%%I\n\nCREATE TABLE %%I.%%I (\n%%s\n);\n'',
                    %L, %L, %L, %L,
                    columns_def
                ) as create_statement
            FROM table_info',
            m.table_name,
            m.schema_name,
            m.schema_name, m.table_name, m.schema_name, m.table_name
        )
    ) AS t(column_count bigint, table_comment text, create_statement text)
) as table_details;

-- Debug: Check results before JSON export
SELECT 'Results before JSON export:' as debug_step;
SELECT * FROM temp_comparison_results;

-- Export results to JSON file
COPY (
    SELECT json_agg(
        json_build_object(
            'schema_name', schema_name,
            'table_name', table_name,
            'full_name', schema_name || '.' || table_name,
            'column_count', column_count,
            'description', description,
            'create_statement', create_statement
        )
    )
    FROM temp_comparison_results
) TO 'A:\Aries Enterprise\wisdom\02_Analysis\Database\Scripts\compare_results.json';

-- Clean up connection
DO $$
BEGIN
    PERFORM dblink_disconnect('source_conn');
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;
