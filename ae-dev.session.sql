-- Check available schemas
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast');

-- Let's see what tables we actually have
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname IN ('public', 'dmeworks', 'repository')
ORDER BY schemaname, tablename;

-- Check exact table names for CMN forms
SELECT schemaname, tablename 
FROM pg_tables 
WHERE tablename LIKE '%cmn%' OR tablename LIKE '%form%'
ORDER BY schemaname, tablename;

-- Check if we have customers table
SELECT schemaname, tablename 
FROM pg_tables 
WHERE tablename IN ('customers', 'patients')
ORDER BY schemaname, tablename;