# Stored Procedures Technical Specification
Version: 1.0
Last Updated: 2024-12-15

## System Architecture

### Base Implementation
All procedures inherit from `BaseProcedure` class providing:
- Async execution support
- Transaction management
- Error handling
- Result tracking

### Directory Structure
```
server/app/procedures/
├── order/
│   ├── internal_process.py
│   ├── internal_balance.py
│   └── fix_policies.py
├── purchase/
│   └── update_totals.py
├── inventory/
│   ├── clone_item.py
│   └── transaction_cleanup.py
├── serial/
│   └── add_transaction.py
├── mir/
│   └── update_customer.py
└── scheduling/
    └── next_dos.py
```

## Technical Details

### 1. Order Processing System
#### OrderInternalProcess
- **Purpose**: Handles order processing and invoice generation
- **Key Methods**:
  - `_execute(order_id, billing_month, billing_flags, invoice_date)`
  - `_create_invoice(order, invoice_date)`
  - `_get_order_details(order_id, billing_month, billing_flags)`
- **Dependencies**:
  - SQLAlchemy ORM
  - Decimal for financial calculations
  - DateTime for billing periods

#### OrderInternalBalance
- **Purpose**: Updates order financial calculations
- **Key Methods**:
  - `_calculate_totals(order_id)`
  - `_update_details_balance(order_detail)`
- **Dependencies**:
  - SQLAlchemy for aggregations
  - Transaction management

### 2. Purchase Order System
#### PurchaseOrderTotals
- **Purpose**: Manages purchase order calculations
- **Key Methods**:
  - `_get_line_totals(po_id)`
  - `_calculate_tax(subtotal, tax_rate)`
- **Dependencies**:
  - Financial calculation utilities
  - Tax rate configuration

### 3. Inventory Management
#### InventoryItemCloner
- **Purpose**: Creates inventory item copies
- **Key Methods**:
  - `_clone_base_item(source, override_fields)`
  - `_clone_relationships(source, target)`
- **Dependencies**:
  - Deep copy utilities
  - Relationship management

#### InventoryTransactionCleanup
- **Purpose**: Maintains transaction integrity
- **Key Methods**:
  - `_identify_orphans()`
  - `_cleanup_transactions()`
- **Dependencies**:
  - Transaction logging
  - Data integrity checks

### 4. Serial Number Management
#### SerialTransactionAdder
- **Purpose**: Manages serial number transactions
- **Key Methods**:
  - `_add_transaction(serial_number, type)`
  - `_update_status(serial_number, status)`
- **Dependencies**:
  - Serial number validation
  - Status tracking

### 5. Medical Information Records
#### CustomerMIRUpdater
- **Purpose**: Updates medical information records
- **Key Methods**:
  - `_validate_customer(customer)`
  - `_update_mir_flags(customer)`
- **Dependencies**:
  - Customer validation
  - Insurance verification

### 6. Scheduling Utilities
#### GetNextDosFrom
- **Purpose**: Calculates next service dates
- **Key Methods**:
  - `get_next_dos_from(from_date, to_date, frequency)`
  - `validate_frequency(frequency)`
- **Dependencies**:
  - Date utilities
  - Frequency patterns

## Error Handling
- All procedures implement comprehensive error handling
- Errors are logged with appropriate detail level
- Transactions are rolled back on failure

## Performance Considerations
- Async operations for long-running processes
- Optimized database queries
- Proper indexing recommendations

## Security
- Input validation on all parameters
- SQL injection prevention
- Access control integration

## Monitoring
- Logging implemented for all critical operations
- Performance metrics tracking
- Error rate monitoring

## Testing Strategy
- Unit tests for all procedures
- Integration tests for workflows
- Performance testing for critical paths
