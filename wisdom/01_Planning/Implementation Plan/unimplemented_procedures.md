# Unimplemented Stored Procedures

This document lists all stored procedures that still need to be implemented in Python, organized by domain.

## Order Domain
1. `Order_InternalProcess` (28.sql)
   - Purpose: Internal order processing with invoice generation
   - Dependencies: GetAmountMultiplier, GetAllowableAmount, GetBillableAmount, OrderMustBeSkipped, InvoiceMustBeSkipped, GetNextDosTo, GetInvoiceModifier, OrderMustBeClosed, Order_ConvertDepositsIntoPayments
   - Priority: High (Core business logic)

2. `Order_InternalUpdateBalance` (35.sql)
   - Purpose: Updates order balance calculations
   - Dependencies: Invoice and Order tables
   - Priority: High (Financial accuracy)

3. `fixOrderPolicies` (30.sql)
   - Purpose: Fixes insurance policy references in orders
   - Dependencies: Customer insurance data
   - Priority: Medium (Data consistency)

## Purchase Domain
4. `PurchaseOrder_UpdateTotals` (29.sql)
   - Purpose: Updates purchase order totals
   - Dependencies: Purchase order line items
   - Priority: High (Financial accuracy)

## Inventory Domain
5. `InventoryItem_Clone` (32.sql)
   - Purpose: Creates a copy of an inventory item
   - Dependencies: Inventory tables
   - Priority: Medium (Operational support)

6. `inventory_transaction_order_cleanup` (p2.sql)
   - Purpose: Cleans up orphaned inventory transactions
   - Dependencies: Order and transaction tables
   - Priority: Low (Maintenance)

## Serial Number Domain
7. `serial_add_transaction` (44.sql)
   - Purpose: Adds serial number transactions
   - Dependencies: Serial number tracking system
   - Priority: High (Asset tracking)

## MIR (Medical Information Record) Domain
8. `mir_update_cmnform` (34.sql)
   - Purpose: Updates Certificate of Medical Necessity forms
   - Dependencies: CMN form data
   - Priority: High (Compliance)

9. `mir_update_customer` (42.sql)
   - Purpose: Updates customer MIR flags
   - Dependencies: Customer data
   - Priority: High (Data integrity)

## Billing Domain
10. `retailinvoice_addpayments` (37.sql)
    - Purpose: Adds payments to retail invoices
    - Dependencies: Payment processing system
    - Priority: High (Financial operations)

## Utility Functions
11. `GetQuantityMultiplier` (31.sql)
    - Purpose: Calculates quantity multipliers for billing
    - Dependencies: None (Pure calculation)
    - Priority: High (Core business logic)

12. `GetNextDosFrom` (p1.sql)
    - Purpose: Calculates next DOS date based on frequency
    - Dependencies: None (Pure calculation)
    - Priority: High (Scheduling logic)

## Implementation Notes

### Priority Levels
- High: Critical for core business operations
- Medium: Important but not blocking core operations
- Low: Nice to have, maintenance or cleanup

### Implementation Order
1. Start with core business logic (High priority)
2. Move to operational support (Medium priority)
3. Finally implement maintenance functions (Low priority)

### Testing Requirements
1. Unit tests for each procedure
2. Integration tests for procedures with dependencies
3. Edge case testing
4. Performance testing for complex procedures

### Documentation Needs
1. Business logic documentation
2. Parameter validation rules
3. Error handling specifications
4. Usage examples

## Next Steps
1. Begin implementation of high-priority procedures
2. Create test cases for each procedure
3. Document business rules and edge cases
4. Review implementations with stakeholders
