# Trigger Analysis: tbl_invoice_transaction_beforeinsert

## Current Implementation

### Trigger Overview
- **Name**: tbl_invoice_transaction_beforeinsert
- **Type**: BEFORE INSERT
- **Table**: c01.tbl_invoice_transaction
- **Language**: plpgsql

### Functionality
The trigger handles three types of invoice adjustments:
1. **Adjust Allowable**: Updates AllowableAmount in invoicedetails
2. **Adjust Customary**: Updates BillableAmount in invoicedetails
3. **Adjust Taxes**: Updates Taxes in invoicedetails

### Key Features
1. **Transaction Type Lookup**
   ```sql
   SELECT Name FROM c01.tbl_invoice_transactiontype
   WHERE ID = NEW.TransactionTypeID;
   ```

2. **Value Comparison**
   - Uses 0.001 tolerance for floating-point comparisons
   ```sql
   IF ABS(V_OldValue - NEW.Amount) > 0.001 THEN
   ```

3. **Audit Trail**
   - Stores previous values in Comments field
   ```sql
   NEW.Comments := CONCAT('Previous Value=', V_OldValue);
   ```

4. **Quantity Tracking**
   - Maintains quantity consistency across transactions

## Migration Strategy

### 1. Modern PostgreSQL Implementation
```sql
CREATE OR REPLACE FUNCTION billing.invoice_transaction_before_insert()
    RETURNS trigger
    LANGUAGE plpgsql
AS $$
DECLARE
    v_old_value numeric(18,2) := 0;
    v_quantity double precision := 0;
    v_tran_type text;
BEGIN
    -- Use ENUM instead of lookup table
    SELECT name INTO v_tran_type 
    FROM billing.invoice_transaction_types 
    WHERE id = NEW.transaction_type_id;

    -- Use CASE statement for cleaner logic
    CASE v_tran_type
        WHEN 'adjust_allowable' THEN
            PERFORM billing.adjust_invoice_amount(
                NEW.invoice_details_id,
                NEW.amount,
                'allowable_amount'
            );
        WHEN 'adjust_customary' THEN
            PERFORM billing.adjust_invoice_amount(
                NEW.invoice_details_id,
                NEW.amount,
                'billable_amount'
            );
        WHEN 'adjust_taxes' THEN
            PERFORM billing.adjust_invoice_amount(
                NEW.invoice_details_id,
                NEW.amount,
                'taxes'
            );
    END CASE;

    RETURN NEW;
END;
$$;
```

### 2. Supporting Functions
```sql
CREATE OR REPLACE FUNCTION billing.adjust_invoice_amount(
    p_invoice_details_id bigint,
    p_new_amount numeric(18,2),
    p_field_name text
) RETURNS void AS $$
DECLARE
    v_old_value numeric(18,2);
    v_quantity double precision;
BEGIN
    -- Get current values
    EXECUTE format('
        SELECT %I, quantity 
        FROM billing.invoice_details 
        WHERE id = $1', p_field_name)
    INTO v_old_value, v_quantity
    USING p_invoice_details_id;

    -- Update if different
    IF abs(v_old_value - p_new_amount) > 0.001 THEN
        EXECUTE format('
            UPDATE billing.invoice_details 
            SET %I = $1 
            WHERE id = $2', p_field_name)
        USING p_new_amount, p_invoice_details_id;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

### 3. Audit Implementation
```sql
CREATE TABLE billing.invoice_adjustments_audit (
    id bigserial PRIMARY KEY,
    invoice_details_id bigint NOT NULL,
    field_name text NOT NULL,
    old_value numeric(18,2) NOT NULL,
    new_value numeric(18,2) NOT NULL,
    changed_at timestamptz NOT NULL DEFAULT current_timestamp,
    changed_by uuid NOT NULL REFERENCES core.users(id),
    CONSTRAINT fk_invoice_details
        FOREIGN KEY (invoice_details_id)
        REFERENCES billing.invoice_details(id)
);
```

## Migration Considerations

1. **Data Integrity**
   - Ensure all transaction types are migrated correctly
   - Validate audit trail preservation
   - Test floating-point comparisons

2. **Performance**
   - Add appropriate indexes
   - Consider partitioning for audit table
   - Monitor trigger overhead

3. **Security**
   - Implement row-level security
   - Add audit logging
   - Validate permissions

4. **Testing**
   - Unit tests for each adjustment type
   - Performance testing under load
   - Validation of audit trail

## Implementation Steps

1. **Phase 1: Schema Setup**
   - Create new schemas and tables
   - Set up audit infrastructure
   - Implement ENUMs for transaction types

2. **Phase 2: Function Migration**
   - Create new trigger and supporting functions
   - Add error handling
   - Implement audit logging

3. **Phase 3: Data Migration**
   - Migrate existing transactions
   - Validate audit history
   - Test all transaction types

4. **Phase 4: Validation**
   - Compare old vs new implementations
   - Performance testing
   - Security validation

## Recommendations

1. **Use Native PostgreSQL Features**
   - ENUMs for transaction types
   - JSONB for extended metadata
   - Temporal tables for history

2. **Improve Error Handling**
   - Add detailed error messages
   - Implement retry logic
   - Add monitoring

3. **Enhance Audit Trail**
   - Add more context to changes
   - Include user information
   - Support compliance requirements

4. **Optimize Performance**
   - Add appropriate indexes
   - Use prepared statements
   - Implement caching where appropriate
