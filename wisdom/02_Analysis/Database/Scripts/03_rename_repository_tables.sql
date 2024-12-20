-- Rename Script for repository schema
-- Phase 1: Remove 'tbl_' prefix
-- Generated: 2024-12-16

BEGIN;

-- First, show the changes that will be made
SELECT 
    table_schema,
    table_name as current_name,
    regexp_replace(table_name, '^tbl_(.+)$', '\1') as new_name
FROM information_schema.tables 
WHERE table_schema = 'repository'
AND table_type = 'BASE TABLE'
AND table_name LIKE 'tbl_%'
ORDER BY table_name;

-- Phase 1: Remove 'tbl_' prefix
ALTER TABLE repository.tbl_batches RENAME TO batches;
ALTER TABLE repository.tbl_certificates RENAME TO certificates;
ALTER TABLE repository.tbl_companies RENAME TO companies;
ALTER TABLE repository.tbl_globals RENAME TO globals;
ALTER TABLE repository.tbl_regions RENAME TO regions;
ALTER TABLE repository.tbl_variables RENAME TO variables;

COMMIT;

-- To rollback in case of issues:
/*
BEGIN;
ALTER TABLE repository.batches RENAME TO tbl_batches;
ALTER TABLE repository.certificates RENAME TO tbl_certificates;
ALTER TABLE repository.companies RENAME TO tbl_companies;
ALTER TABLE repository.globals RENAME TO tbl_globals;
ALTER TABLE repository.regions RENAME TO tbl_regions;
ALTER TABLE repository.variables RENAME TO tbl_variables;
COMMIT;
*/
