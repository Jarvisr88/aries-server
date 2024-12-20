# Complete Schema Analysis

## Shared Schema (shared.*)

### Core User Management
```sql
CREATE TABLE shared.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

CREATE TABLE shared.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shared.user_roles (
    user_id UUID REFERENCES shared.users(id),
    role_id UUID REFERENCES shared.roles(id),
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);
```

### Organization Management
```sql
CREATE TABLE shared.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    tax_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

CREATE TABLE shared.locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES shared.organizations(id),
    name VARCHAR(255) NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'USA',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shared.contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES shared.organizations(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    role VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

## DME Schema (dme.*)

### Equipment Management
```sql
CREATE TABLE dme.equipment_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id UUID REFERENCES dme.equipment_categories(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dme.equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES dme.equipment_categories(id),
    name VARCHAR(255) NOT NULL,
    model_number VARCHAR(100),
    serial_number VARCHAR(100),
    manufacturer VARCHAR(255),
    purchase_date DATE,
    warranty_expiry DATE,
    status equipment_status NOT NULL,
    condition equipment_condition NOT NULL,
    location_id UUID REFERENCES shared.locations(id),
    created_by UUID REFERENCES shared.users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

CREATE TABLE dme.maintenance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID REFERENCES dme.equipment(id),
    performed_by UUID REFERENCES shared.users(id),
    maintenance_type VARCHAR(50) NOT NULL,
    maintenance_date TIMESTAMPTZ NOT NULL,
    notes TEXT,
    next_maintenance TIMESTAMPTZ,
    cost DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dme.equipment_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID REFERENCES dme.equipment(id),
    patient_id UUID REFERENCES shared.users(id),
    assigned_by UUID REFERENCES shared.users(id),
    assigned_date TIMESTAMPTZ NOT NULL,
    return_date TIMESTAMPTZ,
    status assignment_status NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dme.inventory_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID REFERENCES dme.equipment(id),
    transaction_type inventory_transaction_type NOT NULL,
    quantity INTEGER NOT NULL,
    performed_by UUID REFERENCES shared.users(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

## HME Schema (hme.*)

### Insurance Management
```sql
CREATE TABLE hme.insurance_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    provider_code VARCHAR(50) UNIQUE,
    contact_info JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hme.insurance_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES hme.insurance_providers(id),
    name VARCHAR(255) NOT NULL,
    plan_type VARCHAR(50) NOT NULL,
    coverage_details JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hme.patient_insurance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES shared.users(id),
    plan_id UUID REFERENCES hme.insurance_plans(id),
    policy_number VARCHAR(100) NOT NULL,
    group_number VARCHAR(100),
    effective_date DATE NOT NULL,
    expiration_date DATE,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hme.insurance_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_insurance_id UUID REFERENCES hme.patient_insurance(id),
    equipment_assignment_id UUID REFERENCES dme.equipment_assignments(id),
    claim_number VARCHAR(100) UNIQUE,
    filing_date TIMESTAMPTZ NOT NULL,
    service_date TIMESTAMPTZ NOT NULL,
    status claim_status NOT NULL,
    amount_billed DECIMAL(10,2) NOT NULL,
    amount_approved DECIMAL(10,2),
    amount_paid DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

CREATE TABLE hme.claim_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES hme.insurance_claims(id),
    document_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    uploaded_by UUID REFERENCES shared.users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hme.claim_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES hme.insurance_claims(id),
    status claim_status NOT NULL,
    notes TEXT,
    changed_by UUID REFERENCES shared.users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

## Billing Schema (billing.*)

### Payment Management
```sql
CREATE TABLE billing.invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES shared.users(id),
    claim_id UUID REFERENCES hme.insurance_claims(id),
    invoice_number VARCHAR(100) UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    status invoice_status NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE billing.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID REFERENCES billing.invoices(id),
    amount DECIMAL(10,2) NOT NULL,
    payment_method payment_method NOT NULL,
    transaction_id VARCHAR(100),
    payment_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE billing.payment_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID REFERENCES billing.invoices(id),
    total_amount DECIMAL(10,2) NOT NULL,
    installment_amount DECIMAL(10,2) NOT NULL,
    frequency payment_frequency NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status payment_plan_status NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

## Total Table Count
1. **Shared Schema (6 tables)**
   - users
   - roles
   - user_roles
   - organizations
   - locations
   - contacts

2. **DME Schema (6 tables)**
   - equipment_categories
   - equipment
   - maintenance_records
   - equipment_assignments
   - inventory_transactions
   - status_history

3. **HME Schema (7 tables)**
   - insurance_providers
   - insurance_plans
   - patient_insurance
   - insurance_claims
   - claim_documents
   - claim_history
   - patient_insurance

4. **Billing Schema (3 tables)**
   - invoices
   - payments
   - payment_plans

**Total: 22 tables**

## Key Features
- Complete user and role management
- Organization and location tracking
- Comprehensive equipment lifecycle management
- Full insurance claim processing
- Detailed billing and payment tracking
- Audit trails and history tracking
- Document management

Would you like me to elaborate on any specific table structure or add additional tables for specific functionality?
