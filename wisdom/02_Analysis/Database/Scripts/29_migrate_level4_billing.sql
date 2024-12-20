-- Migration Script - Level 4.13 (Billing and Payment Management)
-- Generated: 2024-12-19
-- Description: Creates billing, payment, and financial tracking tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS payment_allocations CASCADE;
DROP TABLE IF EXISTS payment_transactions CASCADE;
DROP TABLE IF EXISTS payment_methods CASCADE;
DROP TABLE IF EXISTS billing_schedules CASCADE;
DROP TABLE IF EXISTS billing_cycles CASCADE;
DROP TABLE IF EXISTS billing_accounts CASCADE;

-- Level 4.35: Billing Configuration
CREATE TABLE IF NOT EXISTS billing_cycles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    frequency_type VARCHAR(20) NOT NULL,
    frequency_interval INTEGER NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_billing_cycle_name UNIQUE (name),
    CONSTRAINT chk_billing_cycle_frequency CHECK (
        frequency_type IN ('daily', 'weekly', 'monthly', 'yearly') AND
        frequency_interval > 0
    )
);

CREATE TABLE IF NOT EXISTS billing_accounts (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    account_number VARCHAR(50) NOT NULL UNIQUE,
    billing_cycle_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    credit_limit DECIMAL(10,2),
    current_balance DECIMAL(10,2) DEFAULT 0,
    last_invoice_date DATE,
    next_invoice_date DATE,
    payment_terms VARCHAR(50),
    payment_due_days INTEGER,
    auto_pay BOOLEAN DEFAULT false,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_billing_account_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_billing_account_cycle FOREIGN KEY (billing_cycle_id) REFERENCES billing_cycles(id),
    CONSTRAINT chk_billing_account_amounts CHECK (
        (credit_limit IS NULL OR credit_limit > 0) AND
        current_balance IS NOT NULL
    ),
    CONSTRAINT chk_billing_account_terms CHECK (
        payment_due_days > 0 OR payment_due_days IS NULL
    )
);

-- Level 4.36: Payment Methods
CREATE TABLE IF NOT EXISTS payment_methods (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    method_type VARCHAR(50) NOT NULL,
    provider VARCHAR(50),
    account_number VARCHAR(50),
    expiry_date DATE,
    is_default BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    verification_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    billing_address_id INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_payment_method_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT chk_payment_method_type CHECK (
        method_type IN ('credit_card', 'bank_account', 'ach', 'wire_transfer', 'other')
    )
);

-- Level 4.37: Payment Processing
CREATE TABLE IF NOT EXISTS payment_transactions (
    id SERIAL PRIMARY KEY,
    billing_account_id INTEGER NOT NULL,
    payment_method_id INTEGER,
    transaction_number VARCHAR(50) NOT NULL UNIQUE,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'pending',
    processed_date TIMESTAMP,
    settlement_date TIMESTAMP,
    reference_number VARCHAR(50),
    authorization_code VARCHAR(50),
    response_code VARCHAR(20),
    response_message TEXT,
    gateway_response JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_payment_transaction_account FOREIGN KEY (billing_account_id) REFERENCES billing_accounts(id),
    CONSTRAINT fk_payment_transaction_method FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id),
    CONSTRAINT chk_payment_transaction_amount CHECK (amount > 0),
    CONSTRAINT chk_payment_transaction_type CHECK (
        transaction_type IN ('payment', 'refund', 'chargeback', 'adjustment')
    )
);

CREATE TABLE IF NOT EXISTS payment_allocations (
    id SERIAL PRIMARY KEY,
    payment_transaction_id INTEGER NOT NULL,
    invoice_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    allocation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    CONSTRAINT fk_payment_allocation_transaction FOREIGN KEY (payment_transaction_id) REFERENCES payment_transactions(id),
    CONSTRAINT fk_payment_allocation_invoice FOREIGN KEY (invoice_id) REFERENCES invoice_forms(id),
    CONSTRAINT chk_payment_allocation_amount CHECK (amount > 0)
);

-- Level 4.38: Billing Schedules
CREATE TABLE IF NOT EXISTS billing_schedules (
    id SERIAL PRIMARY KEY,
    billing_account_id INTEGER NOT NULL,
    schedule_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    next_run_date DATE NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    day_of_month INTEGER,
    day_of_week INTEGER,
    amount DECIMAL(10,2),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    last_run_date DATE,
    last_run_status VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_billing_schedule_account FOREIGN KEY (billing_account_id) REFERENCES billing_accounts(id),
    CONSTRAINT chk_billing_schedule_dates CHECK (
        start_date <= next_run_date AND
        (end_date IS NULL OR end_date >= start_date)
    ),
    CONSTRAINT chk_billing_schedule_frequency CHECK (
        frequency IN ('daily', 'weekly', 'monthly', 'yearly')
    ),
    CONSTRAINT chk_billing_schedule_day_month CHECK (
        (day_of_month IS NULL OR (day_of_month >= 1 AND day_of_month <= 31))
    ),
    CONSTRAINT chk_billing_schedule_day_week CHECK (
        (day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6))
    )
);

-- Add indexes for better performance
CREATE INDEX idx_billing_cycles_active ON billing_cycles(is_active);
CREATE INDEX idx_billing_cycles_frequency ON billing_cycles(frequency_type, frequency_interval);

CREATE INDEX idx_billing_accounts_customer ON billing_accounts(customer_id);
CREATE INDEX idx_billing_accounts_number ON billing_accounts(account_number);
CREATE INDEX idx_billing_accounts_cycle ON billing_accounts(billing_cycle_id);
CREATE INDEX idx_billing_accounts_dates ON billing_accounts(last_invoice_date, next_invoice_date);
CREATE INDEX idx_billing_accounts_status ON billing_accounts(status);

CREATE INDEX idx_payment_methods_customer ON payment_methods(customer_id);
CREATE INDEX idx_payment_methods_type ON payment_methods(method_type);
CREATE INDEX idx_payment_methods_status ON payment_methods(status);
CREATE INDEX idx_payment_methods_default ON payment_methods(is_default);

CREATE INDEX idx_payment_transactions_account ON payment_transactions(billing_account_id);
CREATE INDEX idx_payment_transactions_method ON payment_transactions(payment_method_id);
CREATE INDEX idx_payment_transactions_number ON payment_transactions(transaction_number);
CREATE INDEX idx_payment_transactions_dates ON payment_transactions(processed_date, settlement_date);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(status);

CREATE INDEX idx_payment_allocations_transaction ON payment_allocations(payment_transaction_id);
CREATE INDEX idx_payment_allocations_invoice ON payment_allocations(invoice_id);
CREATE INDEX idx_payment_allocations_date ON payment_allocations(allocation_date);

CREATE INDEX idx_billing_schedules_account ON billing_schedules(billing_account_id);
CREATE INDEX idx_billing_schedules_dates ON billing_schedules(start_date, end_date, next_run_date);
CREATE INDEX idx_billing_schedules_active ON billing_schedules(is_active);

-- Add comments for documentation
COMMENT ON TABLE billing_cycles IS 'Billing cycle configurations';
COMMENT ON TABLE billing_accounts IS 'Customer billing accounts';
COMMENT ON TABLE payment_methods IS 'Stored payment methods';
COMMENT ON TABLE payment_transactions IS 'Payment transaction records';
COMMENT ON TABLE payment_allocations IS 'Payment to invoice allocations';
COMMENT ON TABLE billing_schedules IS 'Automated billing schedules';

-- Add trigger for payment allocation balance update
CREATE OR REPLACE FUNCTION update_billing_account_balance()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE billing_accounts
        SET current_balance = current_balance - NEW.amount
        WHERE id = (
            SELECT billing_account_id
            FROM payment_transactions
            WHERE id = NEW.payment_transaction_id
        );
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE billing_accounts
        SET current_balance = current_balance + OLD.amount
        WHERE id = (
            SELECT billing_account_id
            FROM payment_transactions
            WHERE id = OLD.payment_transaction_id
        );
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_account_balance_on_payment
    AFTER INSERT OR DELETE ON payment_allocations
    FOR EACH ROW
    EXECUTE FUNCTION update_billing_account_balance();

COMMIT;
