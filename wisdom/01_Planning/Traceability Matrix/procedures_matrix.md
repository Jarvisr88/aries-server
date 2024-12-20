# Procedures Traceability Matrix

## Overview
This matrix tracks the implementation status of all stored procedures and functions in the Aries Enterprise system.

## Status Indicators
- ✅ Implemented
- 🔄 In Progress
- ⚠️ Needs Review
- ❌ Not Started

## Priority 1 Procedures (Core Business Logic)

| Procedure Name | Implementation | Location | Purpose | Status |
|---------------|----------------|-----------|---------|---------|
| `Invoice_AddSubmitted` | ✅ | `billing/invoice_submission.py` | Handles insurance submissions | Implemented with batch support |
| `InvoiceDetails_RecalculateInternals_Single` | ✅ | `billing/recalculate.py` | Recalculates invoice totals | Implemented with full balance tracking |
| `InvoiceDetails_InternalAddSubmitted` | ✅ | `billing/internal_submission.py` | Creates submission transactions | Implemented with insurance levels |
| `InvoiceDetails_InternalReflag` | ✅ | `billing/internal_reflag.py` | Handles internal reflagging | Implemented with audit trail |
| `mir_update_customer_insurance` | ✅ | `customer/insurance_mir.py` | Updates insurance MIR flags | Implemented with field validation |
| `mir_update_facility` | ✅ | `facility/mir_update.py` | Updates facility MIR flags | Implemented with field validation |
| `mir_update_orderdetails` | ✅ | `mir/update_orderdetails.py` | Updates MIR flags for orders | Implemented with validation rules |
| `order_process_2` | ✅ | `order/process.py` | Processes orders and invoices | Implemented with full calculation chain |
| `serial_order_refresh` | ✅ | `order/serial_refresh.py` | Refreshes serial transactions | Implemented with priority handling |
| `GetBillableAmount` | ✅ | `billing/billable_amount.py` | Calculates billable amounts | Implemented with all rental types |
| `inventory_order_refresh` | ✅ | `inventory/order_refresh.py` | Refreshes inventory for orders | Implemented with quantity tracking |
| `inventory_refresh` | ✅ | `inventory/refresh.py` | Updates inventory quantities | Implemented with transaction history |
| `order_update_dos` | ✅ | `order/update_dos.py` | Updates order DOS | Implemented with quantity recalc |
| `GetInvoiceModifier` | ✅ | `billing/invoice_modifier.py` | Gets billing modifiers | Implemented with capped rental rules |
| `GetMultiplier` | ✅ | `billing/multiplier.py` | Calculates billing multipliers | Implemented with all frequencies |
| `inventory_po_refresh` | ✅ | `inventory/po_refresh.py` | Refreshes PO inventory | Implemented with quantity tracking |
| `Invoice_InternalUpdateBalance` | ✅ | `billing/internal_balance.py` | Updates invoice balances | Implemented with detail summation |
| `InvoiceDetails_InternalWriteoffBalance` | ✅ | `billing/internal_writeoff.py` | Handles balance writeoffs | Implemented with audit trail |
| `serial_transfer` | ✅ | `serial/transfer.py` | Transfers serial numbers | Implemented with transaction verification |
| `serial_update_transaction` | ✅ | `serial/update_transaction.py` | Updates serial transactions | Implemented with status refresh |
| `inventory_transaction_order_refresh` | ✅ | `inventory/transaction_order_refresh.py` | Refreshes order transactions | Implemented with status tracking |
| `process_reoccuring_order` | ✅ | `order/process_recurring.py` | Processes recurring orders | Implemented with billing cycles |
| `fix_serial_transactions` | ✅ | `serial/fix_transactions.py` | Fixes serial transactions | Implemented with chain validation |
| `InvoiceDetails_AddAutoSubmit` | ✅ | `invoice/auto_submit.py` | Adds auto submit transactions | Implemented with insurance validation |
| `InvoiceMustBeSkipped` | ✅ | `invoice/skip_rules.py` | Determines invoice skip rules | Implemented with date-based logic |
| `Order_ConvertDepositsIntoPayments` | ✅ | `order/convert_deposits.py` | Converts deposits to payments | Implemented with XML handling |
| `process_reoccuring_purchaseorder` | ✅ | `purchase/process_recurring.py` | Processes recurring POs | Implemented with order copying |
| `fixInvoicePolicies` | ✅ | `invoice/fix_policies.py` | Fixes insurance policy references | Implemented with both ORM and raw SQL |
| `GetPeriodEnd` | ✅ | `billing/period_calc.py` | Calculates billing periods | Implemented with all frequencies |
| `GetPeriodEnd2` | ✅ | `billing/period_calc.py` | Extends period calculations | Implemented with pickup handling |
| `inventory_transfer` | ✅ | `inventory/transfer.py` | Transfers inventory between warehouses | Implemented with transaction tracking |
| `internal_inventory_transfer` | ✅ | `inventory/transfer.py` | Internal transfer helper | Implemented with quantity validation |

## Priority 2 Procedures (Operational Support)

| Procedure Name | Implementation | Location | Purpose | Status |
|---------------|----------------|-----------|---------|---------|
| `inventory_adjust_2` | ✅ | `inventory/adjust.py` | Adjusts inventory quantities | Implemented with cost tracking |

## Priority 3 Procedures (Reporting and Analytics)

| Procedure Name | Implementation | Location | Purpose | Status |
|---------------|----------------|-----------|---------|---------|
| To be determined | - | - | - | - |

## Billing Procedures

| Procedure Name | SQL Source | Python Implementation | Status | Test Coverage | Dependencies | Notes |
|---------------|------------|----------------------|--------|---------------|--------------|--------|
| GetQuantityMultiplier | 31.sql | app.procedures.billing.quantity_multiplier.get_quantity_multiplier | ✅ Implemented | ✅ 100% | datetime, app.procedures.scheduling.next_dos | Pure calculation function for determining quantity multipliers based on sale/rental type |

## Scheduling Procedures

| Procedure Name | SQL Source | Python Implementation | Status | Test Coverage | Dependencies | Notes |
|---------------|------------|----------------------|--------|---------------|--------------|--------|
| GetNextDosFrom | p1.sql | app.procedures.scheduling.next_dos.get_next_dos_from | ✅ Implemented | ✅ 100% | datetime, dateutil | Pure calculation function for determining next DOS based on frequency pattern |

## Implementation Notes

### Billing Domain
- Full support for multiple insurance levels
- Complex rental calculations implemented
- Audit trail maintenance
- Transaction history tracking

### Inventory Domain
- Real-time quantity tracking
- Purchase order integration
- Serial number management
- Warehouse management

### Order Domain
- Flexible DOS handling
- Quantity conversions
- Status tracking
- Invoice generation

## Testing Status

### Unit Tests
- Basic test coverage implemented
- Need more edge case testing
- Performance testing pending

### Integration Tests
- Basic flow testing complete
- Need more complex scenario testing
- Load testing pending

## Next Steps
1. Continue implementing remaining procedures
2. Add comprehensive unit tests
3. Document business rules
4. Perform security audit
