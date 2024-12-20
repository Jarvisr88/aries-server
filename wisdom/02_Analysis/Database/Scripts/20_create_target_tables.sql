-- Create Target Tables with New Naming Convention
-- Generated: 2024-12-19

BEGIN;

-- CMN Form Tables
CREATE TABLE IF NOT EXISTS public.cmnforms_0102a (
    LIKE public.tbl_cmnform_0102a INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.cmnforms_0102b (
    LIKE public.tbl_cmnform_0102b INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.cmnforms_0203a (
    LIKE public.tbl_cmnform_0203a INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.cmnforms_0203b (
    LIKE public.tbl_cmnform_0203b INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.cmnforms_0302 (
    LIKE public.tbl_cmnform_0302 INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.cmnforms_0404a (
    LIKE public.tbl_cmnform_0404a INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.cmnforms_484 (
    LIKE public.tbl_cmnform_484 INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.cmnforms_uro (
    LIKE public.tbl_cmnform_uro INCLUDING ALL
);

-- Company and Compliance Tables
CREATE TABLE IF NOT EXISTS public.company_types (
    LIKE public.tbl_companytype INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.compliances (
    LIKE public.tbl_compliance INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.compliance_notes (
    LIKE public.tbl_compliance_notes INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.customer_classes (
    LIKE public.tbl_customerclass INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.customer_types (
    LIKE public.tbl_customertype INCLUDING ALL
);

-- Denial and Deposits Tables
CREATE TABLE IF NOT EXISTS public.denials (
    LIKE public.tbl_denial INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.deposits (
    LIKE public.tbl_deposits INCLUDING ALL
);

-- Doctor and Eligibility Tables
CREATE TABLE IF NOT EXISTS public.doctor_types (
    LIKE public.tbl_doctortype INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.eligibility_requests (
    LIKE public.tbl_eligibilityrequest INCLUDING ALL
);

-- Email and File Tables
CREATE TABLE IF NOT EXISTS public.email_templates (
    LIKE public.tbl_email_templates INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.file_attachments (
    LIKE public.tbl_file_attachments INCLUDING ALL
);

-- Insurance and Inventory Tables
CREATE TABLE IF NOT EXISTS public.haos (
    LIKE public.tbl_hao INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.icd10_codes (
    LIKE public.tbl_icd10 INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.icd9_codes (
    LIKE public.tbl_icd9 INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.images (
    LIKE public.tbl_image INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.insurance_company_groups (
    LIKE public.tbl_insurancecompanygroup INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.insurance_company_types (
    LIKE public.tbl_insurancecompanytype INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.insurance_types (
    LIKE public.tbl_insurancetype INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.inventory_transaction_types (
    LIKE public.tbl_inventory_transaction_type INCLUDING ALL
);

-- Invoice Tables
CREATE TABLE IF NOT EXISTS public.invoice_transactions (
    LIKE public.tbl_invoice_transaction INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.invoice_transaction_types (
    LIKE public.tbl_invoice_transactiontype INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.invoice_details (
    LIKE public.tbl_invoicedetails INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.invoice_forms (
    LIKE public.tbl_invoiceform INCLUDING ALL
);

-- Kit Tables
CREATE TABLE IF NOT EXISTS public.kits (
    LIKE public.tbl_kit INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.kit_details (
    LIKE public.tbl_kitdetails INCLUDING ALL
);

-- Legal and Location Tables
CREATE TABLE IF NOT EXISTS public.legal_representatives (
    LIKE public.tbl_legalrep INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.locations (
    LIKE public.tbl_location INCLUDING ALL
);

-- Medical and Notification Tables
CREATE TABLE IF NOT EXISTS public.medical_conditions (
    LIKE public.tbl_medicalconditions INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.notification_queues (
    LIKE public.tbl_notification_queue INCLUDING ALL
);

-- Object and Order Tables
CREATE TABLE IF NOT EXISTS public.objects (
    LIKE public.tbl_object INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS public.order_surveys (
    LIKE public.tbl_order_survey INCLUDING ALL
);

-- Migration Function
CREATE OR REPLACE FUNCTION migrate_table_data(
    source_table text,
    target_table text
) RETURNS void AS $$
BEGIN
    EXECUTE format('INSERT INTO %I SELECT * FROM %I', target_table, source_table);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error migrating data from % to %: %', source_table, target_table, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Migrate Data
SELECT migrate_table_data('tbl_cmnform_0102a', 'cmnforms_0102a');
SELECT migrate_table_data('tbl_cmnform_0102b', 'cmnforms_0102b');
SELECT migrate_table_data('tbl_cmnform_0203a', 'cmnforms_0203a');
SELECT migrate_table_data('tbl_cmnform_0203b', 'cmnforms_0203b');
SELECT migrate_table_data('tbl_cmnform_0302', 'cmnforms_0302');
SELECT migrate_table_data('tbl_cmnform_0404a', 'cmnforms_0404a');
SELECT migrate_table_data('tbl_cmnform_484', 'cmnforms_484');
SELECT migrate_table_data('tbl_cmnform_uro', 'cmnforms_uro');

-- Continue with other tables...
SELECT migrate_table_data('tbl_companytype', 'company_types');
SELECT migrate_table_data('tbl_compliance', 'compliances');
SELECT migrate_table_data('tbl_compliance_notes', 'compliance_notes');
-- ... and so on for all tables

COMMIT;
