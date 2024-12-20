-- Migration Script: Insurance Tables from DMEworks to Public Schema
-- Version: 2024-12-19
-- Description: Migrates insurance-related data from dmeworks schema to public schema
-- Author: Cascade AI

BEGIN;

-- 1. Migrate insurance companies
INSERT INTO public.insurance_companies (
    id,
    name,
    payer_id,
    address1,
    address2,
    city,
    state,
    zip_code,
    phone,
    fax,
    is_active,
    created_at,
    updated_at
)
SELECT 
    id,
    name,
    COALESCE(payerid, id::text),  -- Use ID as payer_id if payerid is null
    address1,
    address2,
    city,
    state,
    zip,
    phone,
    fax,
    true,
    lastupdatedatetime,
    lastupdatedatetime
FROM dmeworks.insurancecompanies;

-- 2. Migrate payers
INSERT INTO public.insurance_payers (
    id,
    payer_code,
    name,
    type,
    contact_info,
    is_active,
    created_at,
    updated_at
)
SELECT 
    id,
    code,
    name,
    'PRIMARY',
    jsonb_build_object(
        'comments', comments,
        'allows_submission', allowssubmission
    ),
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM dmeworks.ability_eligibility_payers;

-- 3. Create default insurance plans for each company
INSERT INTO public.insurance_plans (
    insurance_company_id,
    plan_name,
    plan_type,
    claims_address,
    claims_phone,
    payer_id,
    supports_electronic_filing,
    is_active,
    created_at,
    updated_at
)
SELECT 
    id,
    name || ' - Default Plan',
    'DEFAULT',
    address1,
    phone,
    COALESCE(payerid, id::text),
    true,
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM dmeworks.insurancecompanies;

-- 4. Create default insurance types
INSERT INTO public.insurance_types (
    name,
    description,
    coverage_type,
    is_primary,
    is_active,
    created_at,
    updated_at
)
VALUES 
    ('Medicare', 'Medicare coverage', 'MEDICARE', true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Medicaid', 'Medicaid coverage', 'MEDICAID', false, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Commercial', 'Commercial insurance', 'COMMERCIAL', false, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Workers Comp', 'Workers compensation', 'WORKERS_COMP', false, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 5. Verify Data Migration
DO $$
DECLARE
    source_count INT;
    target_count INT;
BEGIN
    -- Check insurance companies
    SELECT COUNT(*) INTO source_count FROM dmeworks.insurancecompanies;
    SELECT COUNT(*) INTO target_count FROM public.insurance_companies;
    IF source_count != target_count THEN
        RAISE EXCEPTION 'Insurance company count mismatch: % vs %', source_count, target_count;
    END IF;

    -- Check payers
    SELECT COUNT(*) INTO source_count FROM dmeworks.ability_eligibility_payers;
    SELECT COUNT(*) INTO target_count FROM public.insurance_payers;
    IF source_count != target_count THEN
        RAISE EXCEPTION 'Payer count mismatch: % vs %', source_count, target_count;
    END IF;
END $$;

-- 6. Update Sequences
SELECT setval('public.insurance_companies_id_seq', (SELECT MAX(id) FROM public.insurance_companies));
SELECT setval('public.insurance_payers_id_seq', (SELECT MAX(id) FROM public.insurance_payers));
SELECT setval('public.insurance_plans_id_seq', (SELECT MAX(id) FROM public.insurance_plans));
SELECT setval('public.insurance_types_id_seq', (SELECT MAX(id) FROM public.insurance_types));

COMMIT;

-- Post-migration verification queries (run these manually after migration)
/*
SELECT COUNT(*) as company_count FROM public.insurance_companies;
SELECT COUNT(*) as payer_count FROM public.insurance_payers;
SELECT COUNT(*) as plan_count FROM public.insurance_plans;
SELECT COUNT(*) as type_count FROM public.insurance_types;
*/
