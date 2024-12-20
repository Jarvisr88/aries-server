-- Migration Script - Level 4.4 (Invoicing and Payment Tables)
-- Generated: 2024-12-19
-- Description: Creates invoicing and payment-related tables

BEGIN;

-- Level 4.12: Invoice Management
CREATE TABLE IF NOT EXISTS invoice_forms (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) NOT NULL,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_invoice_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_invoice_company FOREIGN KEY (company_id) REFERENCES companies(id),
    CONSTRAINT chk_invoice_amounts CHECK (
        subtotal >= 0 AND
        tax_amount >= 0 AND
        discount_amount >= 0 AND
        total_amount >= 0
    ),
    CONSTRAINT chk_invoice_dates CHECK (invoice_date <= due_date)
);

CREATE TABLE IF NOT EXISTS invoice_details (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    tax_percent DECIMAL(5,2) DEFAULT 0,
    line_total DECIMAL(10,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_invoice_detail_invoice FOREIGN KEY (invoice_id) REFERENCES invoice_forms(id),
    CONSTRAINT fk_invoice_detail_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT chk_invoice_detail_quantity CHECK (quantity > 0),
    CONSTRAINT chk_invoice_detail_amounts CHECK (
        unit_price >= 0 AND
        discount_percent >= 0 AND
        discount_percent <= 100 AND
        tax_percent >= 0 AND
        tax_percent <= 100 AND
        line_total >= 0
    )
);

-- Level 4.13: Payment Plans
CREATE TABLE IF NOT EXISTS payment_plans (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    plan_type VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    number_of_payments INTEGER NOT NULL,
    payment_frequency VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_payment_plan_invoice FOREIGN KEY (invoice_id) REFERENCES invoice_forms(id),
    CONSTRAINT chk_payment_plan_dates CHECK (start_date <= end_date),
    CONSTRAINT chk_payment_plan_amount CHECK (total_amount > 0),
    CONSTRAINT chk_payment_plan_payments CHECK (number_of_payments > 0)
);

CREATE TABLE IF NOT EXISTS payment_plan_payments (
    id SERIAL PRIMARY KEY,
    payment_plan_id INTEGER NOT NULL,
    payment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    payment_date DATE,
    payment_method VARCHAR(50),
    reference_number VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_plan_payment_plan FOREIGN KEY (payment_plan_id) REFERENCES payment_plans(id),
    CONSTRAINT chk_plan_payment_amount CHECK (amount > 0)
);

-- Level 4.14: Transaction Types
CREATE TABLE IF NOT EXISTS invoice_transaction_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    affects_balance VARCHAR(10) CHECK (affects_balance IN ('increase', 'decrease', 'none')),
    requires_approval BOOLEAN DEFAULT false,
    is_system_type BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

-- Add indexes for better performance
CREATE INDEX idx_invoice_forms_customer ON invoice_forms(customer_id);
CREATE INDEX idx_invoice_forms_company ON invoice_forms(company_id);
CREATE INDEX idx_invoice_forms_dates ON invoice_forms(invoice_date, due_date);
CREATE INDEX idx_invoice_forms_number ON invoice_forms(invoice_number);
CREATE INDEX idx_invoice_forms_status ON invoice_forms(status);

CREATE INDEX idx_invoice_details_invoice ON invoice_details(invoice_id);
CREATE INDEX idx_invoice_details_product ON invoice_details(product_id);

CREATE INDEX idx_payment_plans_invoice ON payment_plans(invoice_id);
CREATE INDEX idx_payment_plans_dates ON payment_plans(start_date, end_date);
CREATE INDEX idx_payment_plans_status ON payment_plans(status);

CREATE INDEX idx_plan_payments_plan ON payment_plan_payments(payment_plan_id);
CREATE INDEX idx_plan_payments_dates ON payment_plan_payments(due_date, payment_date);
CREATE INDEX idx_plan_payments_status ON payment_plan_payments(status);

CREATE INDEX idx_invoice_transaction_types_name ON invoice_transaction_types(name);

-- Add comments for documentation
COMMENT ON TABLE invoice_forms IS 'Main invoice records';
COMMENT ON TABLE invoice_details IS 'Line items for invoices';
COMMENT ON TABLE payment_plans IS 'Payment plans for invoices';
COMMENT ON TABLE payment_plan_payments IS 'Individual payments within payment plans';
COMMENT ON TABLE invoice_transaction_types IS 'Types of invoice transactions';

COMMIT;
