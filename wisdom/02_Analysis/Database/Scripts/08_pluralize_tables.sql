-- Pluralization Script for Specific Tables
-- Generated: 2024-12-16

BEGIN;

-- Rename specific tables
-- Note: audit_log skipped as audit_logs already exists
ALTER TABLE IF EXISTS public.customer RENAME TO customers;
ALTER TABLE IF EXISTS public.customer_insurance RENAME TO customer_insurances;
ALTER TABLE IF EXISTS public.doctor RENAME TO doctors;
ALTER TABLE IF EXISTS public.maintenance_log RENAME TO maintenance_logs;
ALTER TABLE IF EXISTS public.maintenance_schedule RENAME TO maintenance_schedules;
ALTER TABLE IF EXISTS public.payment RENAME TO payments;
ALTER TABLE IF EXISTS public.warehouse RENAME TO warehouses;
ALTER TABLE IF EXISTS public.insurance_company RENAME TO insurance_companies;

-- Log the changes
INSERT INTO public.table_rename_log (schema_name, old_name, new_name, validation_type, message, status)
VALUES 
    ('public', 'customer', 'customers', 'manual_pluralization', 'Table renamed', 'SUCCESS'),
    ('public', 'customer_insurance', 'customer_insurances', 'manual_pluralization', 'Table renamed', 'SUCCESS'),
    ('public', 'doctor', 'doctors', 'manual_pluralization', 'Table renamed', 'SUCCESS'),
    ('public', 'maintenance_log', 'maintenance_logs', 'manual_pluralization', 'Table renamed', 'SUCCESS'),
    ('public', 'maintenance_schedule', 'maintenance_schedules', 'manual_pluralization', 'Table renamed', 'SUCCESS'),
    ('public', 'payment', 'payments', 'manual_pluralization', 'Table renamed', 'SUCCESS'),
    ('public', 'warehouse', 'warehouses', 'manual_pluralization', 'Table renamed', 'SUCCESS'),
    ('public', 'insurance_company', 'insurance_companies', 'manual_pluralization', 'Table renamed', 'SUCCESS');

COMMIT;
