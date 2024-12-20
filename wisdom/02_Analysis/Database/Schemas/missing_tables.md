# Missing Tables Analysis
Date: 2024-12-19

## Overview
This document tracks tables that exist in the source schema but are missing from the target schema.

## Status
- Source Schema: `source_schema.sql`
- Target Schema: `target_schema.sql`

## Missing Tables by Category

### CMN Form Tables
1. `tbl_cmnform_0102a` - CMN Form Type 01.02 Part A
2. `tbl_cmnform_0102b` - CMN Form Type 01.02 Part B
3. `tbl_cmnform_0203a` - CMN Form Type 02.03 Part A
4. `tbl_cmnform_0203b` - CMN Form Type 02.03 Part B
5. `tbl_cmnform_0302` - CMN Form Type 03.02
6. `tbl_cmnform_0403b` - CMN Form Type 04.03 Part B
7. `tbl_cmnform_0403c` - CMN Form Type 04.03 Part C
8. `tbl_cmnform_0404c` - CMN Form Type 04.04 Part C
9. `tbl_cmnform_0602b` - CMN Form Type 06.02 Part B
10. `tbl_cmnform_0603b` - CMN Form Type 06.03 Part B
11. `tbl_cmnform_0702a` - CMN Form Type 07.02 Part A
12. `tbl_cmnform_0702b` - CMN Form Type 07.02 Part B
13. `tbl_cmnform_0703a` - CMN Form Type 07.03 Part A
14. `tbl_cmnform_0802` - CMN Form Type 08.02
15. `tbl_cmnform_0902` - CMN Form Type 09.02
16. `tbl_cmnform_0903` - CMN Form Type 09.03
17. `tbl_cmnform_1003` - CMN Form Type 10.03
18. `tbl_cmnform_4842` - CMN Form Type 4842
19. `tbl_cmnform_drorder` - CMN Form Doctor Order Type
20. `tbl_cmnform_uro` - CMN Form Urology Type

### Company and Compliance Tables
1. `tbl_companytype` - Company Type Table
2. `tbl_compliance` - Compliance Table
3. `tbl_compliance_notes` - Compliance Notes Table
4. `tbl_customerclass` - Customer Class Table
5. `tbl_customertype` - Customer Type Table

### Denial and Deposits Tables
1. `tbl_denial` - Denial Table
2. `tbl_deposits` - Deposits Table

### Doctor and Eligibility Tables
1. `tbl_doctortype` - Doctor Type Table
2. `tbl_eligibilityrequest` - Eligibility Request Table

### Email and File Tables
1. `tbl_email_templates` - Email Templates Table
2. `tbl_file_attachments` - File Attachments Table

### Insurance and Inventory Tables
1. `tbl_hao` - Health Account Organization Table
2. `tbl_icd10` - ICD10 Table
3. `tbl_icd9` - ICD9 Table
4. `tbl_image` - Image Table
5. `tbl_insurancecompanygroup` - Insurance Company Group Table
6. `tbl_insurancecompanytype` - Insurance Company Type Table
7. `tbl_insurancetype` - Insurance Type Table
8. `tbl_inventory_transaction_type` - Inventory Transaction Type Table
9. `tbl_invoice_transaction` - Invoice Transaction Table
10. `tbl_invoice_transactiontype` - Invoice Transaction Type Table
11. `tbl_invoicedetails` - Invoice Details Table
12. `tbl_invoiceform` - Invoice Form Table
13. `tbl_kit` - Kit Table
14. `tbl_kitdetails` - Kit Details Table

### Legal and Location Tables
1. `tbl_legalrep` - Legal Representative Table
2. `tbl_location` - Location Table

### Medical and Notification Tables
1. `tbl_medicalconditions` - Medical Conditions Table
2. `tbl_notification_queue` - Notification Queue Table

### Object and Order Tables
1. `tbl_object` - Object Table
2. `tbl_order_survey` - Order Survey Table

### Payer and Payment Tables
1. `tbl_payer` - Payer Table
2. `tbl_paymentplan` - Payment Plan Table
3. `tbl_paymentplan_payments` - Payment Plan Payments Table
4. `tbl_postype` - Payment Type Table

### Predefined and Price Tables
1. `tbl_predefinedtext` - Predefined Text Table
2. `tbl_price_history` - Price History Table
3. `tbl_pricecode` - Price Code Table

### Product and Provider Tables
1. `tbl_product_category` - Product Category Table
2. `tbl_product_history` - Product History Table
3. `tbl_product_price` - Product Price Table
4. `tbl_productgroup` - Product Group Table
5. `tbl_producttype` - Product Type Table
6. `tbl_provider` - Provider Table
7. `tbl_providernumbertype` - Provider Number Type Table

### Purchase and Referral Tables
1. `tbl_purchase_order_details` - Purchase Order Details Table
2. `tbl_purchaseorder` - Purchase Order Table
3. `tbl_referral` - Referral Table
4. `tbl_referraltype` - Referral Type Table

### Relationship and Report Tables
1. `tbl_relationship` - Relationship Table
2. `tbl_report_schedules` - Report Schedules Table

### Sales and Serial Tables
1. `tbl_salesrep` - Sales Representative Table
2. `tbl_serial` - Serial Table
3. `tbl_serial_maintenance` - Serial Maintenance Table
4. `tbl_serial_transaction` - Serial Transaction Table
5. `tbl_serial_transaction_type` - Serial Transaction Type Table

### Session and Shipping Tables
1. `tbl_sessions` - Sessions Table
2. `tbl_shipping_history` - Shipping History Table
3. `tbl_shipping_tracking` - Shipping Tracking Table
4. `tbl_shippingmethod` - Shipping Method Table

### Signature and Submitter Tables
1. `tbl_signaturetype` - Signature Type Table
2. `tbl_submitter` - Submitter Table

### Survey and System Tables
1. `tbl_survey` - Survey Table
2. `tbl_system_settings` - System Settings Table

### Tax and User Tables
1. `tbl_taxrate` - Tax Rate Table
2. `tbl_user_activity_log` - User Activity Log Table
3. `tbl_user_location` - User Location Table
4. `tbl_user_notifications` - User Notifications Table

### Variables and Vendor Tables
1. `tbl_variables` - Variables Table
2. `tbl_vendor` - Vendor Table

## Next Steps
1. Analyze dependencies between tables
2. Create migration scripts for each table
3. Ensure proper data transformation during migration
4. Update related application code to handle new table names

## Dependencies and Relationships
- All tables are related to each other through various foreign key relationships
- Need to ensure foreign key relationships are preserved during migration
- Data in these tables needs to be validated before migration

## Migration Priority
1. High Priority - These tables contain critical data
2. Must be migrated as a complete set to maintain data integrity
3. Requires thorough testing due to complexity of data
