-- Migration Script: DMEworks to Public Schema
-- Version: 2024-12-19
-- Description: Migrates data from dmeworks schema to public schema and removes dmeworks schema
-- Author: Cascade AI

BEGIN;

-- 1. Data Migration
-- Note: Using INSERT ... SELECT to preserve data

-- First create the target tables if they don't exist
CREATE TABLE IF NOT EXISTS public.healthcare_providers (
    id serial NOT NULL,
    first_name varchar(100) NOT NULL,
    last_name varchar(100) NOT NULL,
    middle_name varchar(1),
    license_number varchar(16) NOT NULL,
    license_expiry_date date,
    medicaid_number varchar(16) NOT NULL,
    dea_number varchar(20),
    upin_number varchar(11),
    tax_id varchar(9),
    npi varchar(10),
    pecos_enrolled boolean DEFAULT false,
    address_line1 varchar(100),
    address_line2 varchar(100),
    city varchar(100),
    state varchar(2),
    postal_code varchar(10),
    phone varchar(50),
    phone2 varchar(50),
    fax varchar(50),
    provider_type_id integer,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT healthcare_providers_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.provider_types (
    id serial NOT NULL,
    name varchar(50) NOT NULL,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT provider_types_pkey PRIMARY KEY (id)
);

-- Migrate doctors to healthcare_providers
INSERT INTO public.healthcare_providers (
    id,
    first_name,
    last_name,
    middle_name,
    license_number,
    license_expiry_date,
    medicaid_number,
    dea_number,
    upin_number,
    tax_id,
    npi,
    pecos_enrolled,
    address_line1,
    address_line2,
    city,
    state,
    postal_code,
    phone,
    phone2,
    fax,
    provider_type_id,
    created_at,
    updated_at
)
SELECT 
    id,
    firstname,
    lastname,
    middlename,
    licensenumber,
    licenseexpired,
    medicaidnumber,
    deanumber,
    upinnumber,
    fedtaxid,
    npi,
    pecosenrolled,
    address1,
    address2,
    city,
    state,
    zip,
    phone,
    phone2,
    fax,
    typeid,
    lastupdatedatetime,
    lastupdatedatetime
FROM dmeworks.doctors;

-- Migrate doctor types to provider_types
INSERT INTO public.provider_types (
    id,
    name,
    created_at,
    updated_at
)
SELECT 
    id,
    name,
    lastupdatedatetime,
    lastupdatedatetime
FROM dmeworks.doctortypes;

-- Migrate ICD codes to billing_codes
INSERT INTO public.billing_codes (
    code,
    description,
    code_type,
    effective_date,
    end_date,
    is_active,
    created_at,
    updated_at
)
SELECT 
    code,
    description,
    'ICD10',
    activedate,
    inactivedate,
    true,
    lastupdatedatetime,
    lastupdatedatetime
FROM dmeworks.icd10s
UNION ALL
SELECT 
    code,
    description,
    'ICD9',
    activedate,
    inactivedate,
    true,
    lastupdatedatetime,
    lastupdatedatetime
FROM dmeworks.icd9s;

-- 2. Verify Data Migration
DO $$
DECLARE
    source_count INT;
    target_count INT;
BEGIN
    -- Check healthcare providers
    SELECT COUNT(*) INTO source_count FROM dmeworks.doctors;
    SELECT COUNT(*) INTO target_count FROM public.healthcare_providers;
    IF source_count != target_count THEN
        RAISE EXCEPTION 'Healthcare provider count mismatch: % vs %', source_count, target_count;
    END IF;

    -- Check provider types
    SELECT COUNT(*) INTO source_count FROM dmeworks.doctortypes;
    SELECT COUNT(*) INTO target_count FROM public.provider_types;
    IF source_count != target_count THEN
        RAISE EXCEPTION 'Provider type count mismatch: % vs %', source_count, target_count;
    END IF;

    -- Add more verification as needed
END $$;

-- 3. Update Sequences
SELECT setval('public.healthcare_providers_id_seq', (SELECT MAX(id) FROM public.healthcare_providers));
SELECT setval('public.provider_types_id_seq', (SELECT MAX(id) FROM public.provider_types));

-- 4. Drop DMEworks Schema (only after verifying data migration)
DROP SCHEMA IF EXISTS dmeworks CASCADE;

COMMIT;

-- Post-migration verification queries (run these manually after migration)
/*
SELECT COUNT(*) as provider_count FROM public.healthcare_providers;
SELECT COUNT(*) as provider_type_count FROM public.provider_types;
SELECT COUNT(*) as billing_codes_count FROM public.billing_codes;
*/
