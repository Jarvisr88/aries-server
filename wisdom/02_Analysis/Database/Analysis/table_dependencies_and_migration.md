# Table Dependencies and Migration Analysis
Date: 2024-12-19

## Migration Order Based on Dependencies

### Level 1 - Base Tables (No Dependencies)
1. System and Configuration
   - `tbl_system_settings`
   - `tbl_variables`
   - `tbl_predefinedtext`
   - `tbl_email_templates`

2. Type/Category Tables
   - `tbl_companytype`
   - `tbl_customertype`
   - `tbl_customerclass`
   - `tbl_doctortype`
   - `tbl_insurancetype`
   - `tbl_insurancecompanytype`
   - `tbl_producttype`
   - `tbl_signaturetype`
   - `tbl_referraltype`
   - `tbl_providernumbertype`
   - `tbl_inventory_transaction_type`
   - `tbl_serial_transaction_type`
   - `tbl_invoice_transactiontype`

3. Reference Tables
   - `tbl_icd9`
   - `tbl_icd10`
   - `tbl_medicalconditions`
   - `tbl_relationship`
   - `tbl_pricecode`
   - `tbl_taxrate`

### Level 2 - Primary Entity Tables
1. Company and Location
   - `tbl_location` (depends on: companytype)
   - `tbl_vendor` (depends on: location)
   - `tbl_provider` (depends on: location, providernumbertype)
   - `tbl_insurancecompanygroup`
   - `tbl_hao`

2. Product Related
   - `tbl_product_category`
   - `tbl_productgroup`
   - `tbl_product_price` (depends on: pricecode)
   - `tbl_price_history`
   - `tbl_product_history`

3. User Related
   - `tbl_user_location` (depends on: location)
   - `tbl_user_notifications`
   - `tbl_user_activity_log`
   - `tbl_sessions`

### Level 3 - Dependent Entity Tables
1. CMN Form Tables (depends on: doctors, customers)
   - `tbl_cmnform_0102a`
   - `tbl_cmnform_0102b`
   - `tbl_cmnform_0203a`
   - `tbl_cmnform_0203b`
   - `tbl_cmnform_0302`
   - `tbl_cmnform_0403b`
   - `tbl_cmnform_0403c`
   - `tbl_cmnform_0404c`
   - `tbl_cmnform_0602b`
   - `tbl_cmnform_0603b`
   - `tbl_cmnform_0702a`
   - `tbl_cmnform_0702b`
   - `tbl_cmnform_0703a`
   - `tbl_cmnform_0802`
   - `tbl_cmnform_0902`
   - `tbl_cmnform_0903`
   - `tbl_cmnform_1003`
   - `tbl_cmnform_4842`
   - `tbl_cmnform_drorder`
   - `tbl_cmnform_uro`

2. Inventory and Serial
   - `tbl_kit`
   - `tbl_kitdetails` (depends on: kit)
   - `tbl_serial` (depends on: inventory)
   - `tbl_serial_maintenance` (depends on: serial)
   - `tbl_serial_transaction` (depends on: serial, serial_transaction_type)

3. Orders and Invoices
   - `tbl_order_survey` (depends on: orders)
   - `tbl_invoice_transaction` (depends on: invoices)
   - `tbl_invoicedetails` (depends on: invoices)
   - `tbl_invoiceform` (depends on: invoices)
   - `tbl_shipping_history` (depends on: orders)
   - `tbl_shipping_tracking` (depends on: orders)

4. Payments and Financial
   - `tbl_paymentplan` (depends on: customers)
   - `tbl_paymentplan_payments` (depends on: paymentplan)
   - `tbl_deposits` (depends on: payments)
   - `tbl_denial` (depends on: claims)

5. Compliance and Documentation
   - `tbl_compliance` (depends on: customers)
   - `tbl_compliance_notes` (depends on: compliance)
   - `tbl_file_attachments`
   - `tbl_image`

## Migration Scripts Structure

Each migration script will follow this pattern:
1. Create table with proper schema
2. Migrate data with transformations
3. Add constraints and indexes
4. Verify data integrity

I'll now create the migration scripts in order. Would you like me to:
1. Start with Level 1 tables first?
2. Focus on a specific category of tables?
3. Create the complete set of migration scripts in dependency order?
