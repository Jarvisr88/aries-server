# Stored Procedure Categories

## Billing Procedures
- [x] `Invoice_AddSubmitted` (p5.sql)
- [x] `InvoiceDetails_RecalculateInternals` (69.sql)
- [x] `InvoiceDetails_InternalAddSubmitted` 
- [x] `InvoiceDetails_InternalReflag`
- [x] `Invoice_InternalUpdateBalance`
- [x] `InvoiceDetails_InternalWriteoffBalance`
- [x] `InvoiceDetails_AddAutoSubmit`
- [x] `InvoiceMustBeSkipped`
- [x] `GetBillableAmount`
- [x] `GetInvoiceModifier`
- [x] `GetMultiplier`
- [x] `GetPeriodEnd`
- [x] `GetPeriodEnd2`
- [ ] `GetAllowableAmount` (26.sql)
- [ ] `GetClaimNumber` (28.sql)
- [ ] `GetInvoiceNumber` (34.sql)

## Inventory Procedures
- [x] `inventory_adjust_2`
- [x] `inventory_refresh`
- [x] `inventory_order_refresh`
- [x] `inventory_po_refresh`
- [x] `inventory_transfer`
- [x] `internal_inventory_transfer`
- [ ] `inventory_transaction_refresh` (44.sql)
- [ ] `inventory_warehouse_refresh` (46.sql)

## Order Processing
- [x] `order_process_2`
- [x] `order_update_dos`
- [x] `process_reoccuring_order`
- [x] `Order_ConvertDepositsIntoPayments`
- [ ] `order_internal_refresh` (48.sql)
- [ ] `order_refresh_all` (51.sql)
- [ ] `order_update_mir` (54.sql)

## Serial Number Management
- [x] `serial_order_refresh`
- [x] `serial_transfer`
- [x] `serial_update_transaction`
- [x] `fix_serial_transactions`
- [ ] `serial_add_transaction` (80.sql)
- [ ] `serial_transaction_refresh` (81.sql)

## MIR Updates
- [x] `mir_update_customer_insurance`
- [x] `mir_update_facility`
- [x] `mir_update_orderdetails`
- [ ] `mir_update_customer` (41.sql)
- [ ] `mir_update_doctor` (42.sql)

## Purchase Orders
- [x] `process_reoccuring_purchaseorder`
- [ ] `purchase_order_refresh` (67.sql)
- [ ] `purchase_order_update_mir` (68.sql)

## Customer Management
- [ ] `customer_update_mir` (p10.sql)
- [ ] `customer_update_insurance_mir` (p13.sql)

## Doctor Management
- [ ] `doctor_update_mir` (p18.sql)
- [ ] `doctor_update_pos_mir` (p19.sql)

## Facility Management
- [ ] `facility_update_mir` (p21.sql)
- [ ] `facility_update_pos_mir` (p22.sql)

## System Procedures
- [ ] `system_update_mir` (82.sql)
- [ ] `system_update_pos_mir` (83.sql)

## Status
- Total Procedures: 79
- Implemented: 32
- Remaining: 47
