# Database Migration Analysis

## Source Database Overview

### Schema Count
1. c01 (Primary Schema): ~119 tables
2. Additional Schemas: 16 tables (10 + 6 in other schemas)

### Core Table Categories

1. **Customer Management**
   - tbl_customer
   - tbl_customer_insurance
   - tbl_customer_note
   - Related tables: ~15

2. **Order Management**
   - tbl_order
   - tbl_orderdetails
   - tbl_orderdetails_note
   - Related tables: ~20

3. **Inventory Management**
   - tbl_inventory
   - tbl_inventoryitem
   - tbl_serial
   - Related tables: ~12

4. **Billing & Payments**
   - tbl_invoice
   - tbl_invoicedetails
   - tbl_payment
   - tbl_batchpayment
   - Related tables: ~25

5. **Insurance & Claims**
   - tbl_insurance
   - tbl_claim
   - tbl_authorization
   - Related tables: ~15

6. **Medical Documentation**
   - tbl_cmnform (and related tables)
   - tbl_prescription
   - Related tables: ~20

7. **System Management**
   - tbl_audit_log
   - tbl_batch_log
   - tbl_changes
   - Related tables: ~12

### Function Categories

1. **Invoice Processing**
   - InvoiceDetails_AddPayment
   - InvoiceDetails_RecalculateInternals
   - Related functions: ~10

2. **Order Management**
   - OrderDetails_Create
   - OrderDetails_Update
   - Related functions: ~15

3. **Customer Management**
   - Customer_Create
   - Customer_Update
   - Related functions: ~8

4. **Payment Processing**
   - Payment_Process
   - Payment_Reconcile
   - Related functions: ~12

5. **Batch Operations**
   - Batch_ProcessClaims
   - Batch_ProcessPayments
   - Related functions: ~10

### View Categories

1. **Operational Views**
   - view_orderdetails_core
   - view_invoice_summary
   - Count: ~8

2. **Reporting Views**
   - view_customer_summary
   - view_payment_summary
   - Count: ~6

3. **Administrative Views**
   - view_audit_log
   - view_batch_status
   - Count: ~5

## Target Database Design

### Schema Organization

1. **Core Schema**
```sql
CREATE SCHEMA core;
-- Base tables like users, roles, organizations
```

2. **Medical Schema**
```sql
CREATE SCHEMA medical;
-- Medical-specific tables like prescriptions, CMN forms
```

3. **Billing Schema**
```sql
CREATE SCHEMA billing;
-- Financial tables like invoices, payments
```

4. **Inventory Schema**
```sql
CREATE SCHEMA inventory;
-- Inventory and equipment management
```

5. **Audit Schema**
```sql
CREATE SCHEMA audit;
-- Audit logs and tracking
```

### Modern Features to Add

1. **UUID Primary Keys**
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
```

2. **Temporal Tables**
```sql
valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
valid_to TIMESTAMPTZ NOT NULL DEFAULT 'infinity'
```

3. **JSONB for Flexible Data**
```sql
metadata JSONB,
settings JSONB
```

4. **Enum Types**
```sql
CREATE TYPE order_status AS ENUM ('draft', 'pending', 'approved', 'completed');
```

5. **Full Text Search**
```sql
-- Add for relevant text fields
ADD COLUMN search_vector tsvector
GENERATED ALWAYS AS (
  to_tsvector('english', 
    coalesce(name,'') || ' ' || 
    coalesce(description,'')
  )
) STORED;
```

### Migration Strategy

1. **Data Type Mapping**
   - char/varchar -> text
   - datetime -> timestamptz
   - decimal -> numeric
   - int -> bigint
   - bit -> boolean

2. **Stored Procedure Migration**
   - Move business logic to application layer
   - Use database functions only for data integrity
   - Implement complex calculations in Python

3. **View Migration**
   - Replace views with API endpoints
   - Keep only essential reporting views
   - Use materialized views for performance

4. **Index Strategy**
   - B-tree for exact matches
   - GiST for geometric data
   - GIN for full-text search
   - Partial indexes for filtered queries

5. **Constraint Strategy**
   - Foreign key constraints
   - Check constraints
   - Unique constraints
   - Exclusion constraints

### Performance Considerations

1. **Partitioning**
   - Partition large tables by date
   - Consider range partitioning for historical data

2. **Materialized Views**
   - Create for heavy reporting queries
   - Implement refresh strategy

3. **Indexing Strategy**
   - Covering indexes for common queries
   - Partial indexes for filtered data
   - Expression indexes for computed columns

4. **Vacuum Strategy**
   - Regular vacuum for high-churn tables
   - Analyze strategy for statistics

### Security Implementation

1. **Row Level Security**
```sql
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;
CREATE POLICY policy_name ON table_name
  USING (organization_id = current_setting('app.current_org_id')::uuid);
```

2. **Column Level Encryption**
   - Encrypt sensitive data
   - Use pgcrypto extension

3. **Audit Logging**
   - Track all data changes
   - Maintain change history

### Migration Phases

1. **Phase 1: Schema Migration**
   - Create new schemas
   - Set up base tables
   - Implement constraints

2. **Phase 2: Data Migration**
   - Develop ETL processes
   - Validate data integrity
   - Test migrations

3. **Phase 3: Function Migration**
   - Convert stored procedures
   - Implement in Python
   - Test business logic

4. **Phase 4: View Migration**
   - Create new views
   - Implement API endpoints
   - Test reporting

5. **Phase 5: Optimization**
   - Add indexes
   - Implement partitioning
   - Performance tuning

### Validation Strategy

1. **Data Validation**
   - Row counts
   - Sample comparisons
   - Business logic tests

2. **Performance Validation**
   - Query performance
   - Load testing
   - Concurrent access

3. **Security Validation**
   - Access controls
   - Data encryption
   - Audit logging

## Next Steps

1. Create detailed mapping documents for each table
2. Develop migration scripts
3. Set up test environment
4. Create validation framework
5. Plan cutover strategy
