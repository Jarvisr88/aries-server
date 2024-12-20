-- Pluralization Script for repository schema
-- Phase 2: Convert to plural form
-- Generated: 2024-12-16

BEGIN;

-- First, show the changes that will be made
SELECT 
    table_schema,
    table_name as current_name,
    CASE 
        WHEN table_name LIKE '%y' AND NOT table_name ~ '[aeiou]y$' THEN 
            regexp_replace(table_name, 'y$', 'ies')
        WHEN table_name LIKE '%s' OR table_name LIKE '%x' OR table_name LIKE '%ch' THEN 
            table_name || 'es'
        ELSE 
            table_name || 's'
    END as plural_name
FROM information_schema.tables 
WHERE table_schema = 'repository'
AND table_type = 'BASE TABLE'
AND table_name NOT LIKE '%s'
ORDER BY table_name;

-- Note: All tables are already in plural form after the rename
-- No pluralization needed for:
-- - batches (already plural)
-- - certificates (already plural)
-- - companies (already plural)
-- - globals (already plural)
-- - regions (already plural)
-- - variables (already plural)

COMMIT;
