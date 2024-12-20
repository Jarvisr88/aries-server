# Aries Enterprise Class Dictionary
Version: 1.0
Last Updated: 2024-12-16

## Base Classes

### BaseProcedure
**Location**: `server/app/procedures/base.py`
**Purpose**: Base class for all stored procedures
**Key Methods**:
- `execute(*args, **kwargs)`: Main execution method
- `_pre_execute(*args, **kwargs)`: Pre-execution hook
- `_execute(*args, **kwargs)`: Core execution logic
- `_post_execute(*args, **kwargs)`: Post-execution hook
**Features**:
- Transaction management
- Error handling
- Result tracking
- Async support

## Order Domain

### OrderInternalProcess
**Location**: `server/app/procedures/order/internal_process.py`
**Purpose**: Handles order processing and invoice generation
**Key Methods**:
- `_get_order_details(order_id, billing_month, billing_flags)`
- `_create_invoice(order, invoice_date)`
- `_create_invoice_detail(invoice, order_detail, dos_from, dos_to, amount)`
**Dependencies**:
- OrderMustBeSkipped
- InvoiceMustBeSkipped
- GetNextDosTo

### OrderInternalBalance
**Location**: `server/app/procedures/order/internal_balance.py`
**Purpose**: Updates order balance calculations
**Key Methods**:
- `_calculate_totals(order_id)`
- `_update_details_balance(order_detail)`
**Features**:
- Real-time balance updates
- Transaction history tracking
- Financial calculations

### OrderPolicyFixer
**Location**: `server/app/procedures/order/fix_policies.py`
**Purpose**: Fixes and updates order policies
**Key Methods**:
- `_get_customer_policy(customer_id)`
- `_update_order_policies(order_id)`
**Features**:
- Policy validation
- Insurance integration
- Historical tracking

## Purchase Domain

### PurchaseOrderTotals
**Location**: `server/app/procedures/purchase/update_totals.py`
**Purpose**: Updates purchase order totals
**Key Methods**:
- `_get_line_totals(po_id)`
- `_calculate_tax(subtotal, tax_rate)`
**Features**:
- Line item calculations
- Tax handling
- Discount processing

## Inventory Domain

### InventoryItemCloner
**Location**: `server/app/procedures/inventory/clone_item.py`
**Purpose**: Creates copies of inventory items
**Key Methods**:
- `_clone_base_item(source, override_fields)`
- `_clone_relationships(source, target)`
**Features**:
- Deep copy support
- Relationship management
- Unique field handling

### InventoryTransactionCleanup
**Location**: `server/app/procedures/inventory/transaction_cleanup.py`
**Purpose**: Cleans up orphaned transactions
**Key Methods**:
- `_identify_orphans()`
- `_cleanup_transactions()`
**Features**:
- Data integrity checks
- Transaction validation
- Automated cleanup

## Serial Number Domain

### SerialTransactionAdder
**Location**: `server/app/procedures/serial/add_transaction.py`
**Purpose**: Manages serial number transactions
**Key Methods**:
- `_add_transaction(serial_number, type)`
- `_update_status(serial_number, status)`
**Features**:
- Status tracking
- Transaction history
- Validation rules

## MIR Domain

### CustomerMIRUpdater
**Location**: `server/app/procedures/mir/update_customer.py`
**Purpose**: Updates customer medical information records
**Key Methods**:
- `_validate_customer(customer)`
- `_update_mir_flags(customer)`
**Features**:
- Data validation
- Insurance verification
- Flag management

### CMNFormMIRUpdater
**Location**: `server/app/procedures/mir/update_cmnform.py`
**Purpose**: Updates CMN form medical information
**Key Methods**:
- `_validate_cmnform(form)`
- `_update_mir_data(form)`
**Features**:
- Form validation
- Medical data tracking
- Compliance checks

## Trigger Classes

### InvoiceTransactionTrigger
**Location**: `server/app/triggers/invoice_transaction.py`
**Purpose**: Handles invoice transaction triggers
**Key Methods**:
- `before_insert(transaction)`
- `_get_transaction_type(type_id)`
- `_update_invoice_detail(customer_id, invoice_id, detail_id, field, value)`
**Features**:
- Event handling
- Transaction validation
- Amount adjustments

## Utility Classes

### GetNextDosFrom
**Location**: `server/app/procedures/scheduling/next_dos.py`
**Purpose**: Calculates next service dates
**Key Methods**:
- `get_next_dos_from(from_date, to_date, frequency)`
- `validate_frequency(frequency)`
**Features**:
- Date calculations
- Frequency validation
- Pattern support

## Class Relationships

### Order Processing Flow
```
OrderInternalProcess
├── OrderMustBeSkipped
├── InvoiceMustBeSkipped
└── GetNextDosTo
```

### Inventory Management Flow
```
InventoryItemCloner
└── InventoryTransactionCleanup
    └── SerialTransactionAdder
```

### MIR Update Flow
```
CustomerMIRUpdater
└── CMNFormMIRUpdater
```

## Common Features Across Classes

### Error Handling
- All classes implement comprehensive error handling
- Custom exceptions for specific scenarios
- Error logging and tracking

### Transaction Management
- Automatic transaction handling
- Rollback on failure
- Nested transaction support

### Validation
- Input validation
- Business rule validation
- Data integrity checks

### Logging
- Operation logging
- Error logging
- Audit trail support

### Performance
- Async operations where appropriate
- Optimized database queries
- Bulk operation support

## Best Practices

### Implementation Guidelines
1. All procedures should inherit from BaseProcedure
2. Implement all required hooks (_pre_execute, _execute, _post_execute)
3. Use proper error handling and logging
4. Follow async/await patterns
5. Include comprehensive documentation

### Testing Requirements
1. Unit tests for all classes
2. Integration tests for workflows
3. Edge case coverage
4. Performance testing

### Documentation Standards
1. Clear class and method documentation
2. Usage examples
3. Parameter descriptions
4. Return value specifications

## Maintenance Notes

### Regular Tasks
1. Monitor error logs
2. Check performance metrics
3. Update documentation
4. Review test coverage

### Optimization Opportunities
1. Query optimization
2. Caching strategies
3. Bulk operation implementation
4. Index management
