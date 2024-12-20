-- Migration Script - Level 4.14 (Financial Management)
-- Generated: 2024-12-19
-- Description: Creates financial tracking and accounting tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS journal_entries CASCADE;
DROP TABLE IF EXISTS general_ledger CASCADE;
DROP TABLE IF EXISTS chart_of_accounts CASCADE;
DROP TABLE IF EXISTS accounting_periods CASCADE;
DROP TABLE IF EXISTS tax_rates CASCADE;

-- Level 4.39: Accounting Configuration
CREATE TABLE IF NOT EXISTS tax_rates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    rate DECIMAL(5,2) NOT NULL,
    description TEXT,
    is_compound BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_tax_rate_name UNIQUE (name),
    CONSTRAINT chk_tax_rate CHECK (rate >= 0 AND rate <= 100)
);

CREATE TABLE IF NOT EXISTS accounting_periods (
    id SERIAL PRIMARY KEY,
    period_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    is_adjustment_period BOOLEAN DEFAULT false,
    notes TEXT,
    closed_date TIMESTAMP,
    closed_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_accounting_period_dates UNIQUE (start_date, end_date),
    CONSTRAINT chk_accounting_period_dates CHECK (start_date < end_date)
);

-- Level 4.40: Chart of Accounts
CREATE TABLE IF NOT EXISTS chart_of_accounts (
    id SERIAL PRIMARY KEY,
    account_number VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    account_type VARCHAR(50) NOT NULL,
    parent_account_id INTEGER,
    is_header BOOLEAN DEFAULT false,
    is_control_account BOOLEAN DEFAULT false,
    normal_balance VARCHAR(10) NOT NULL,
    current_balance DECIMAL(15,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_account_parent FOREIGN KEY (parent_account_id) REFERENCES chart_of_accounts(id),
    CONSTRAINT chk_account_type CHECK (
        account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')
    ),
    CONSTRAINT chk_normal_balance CHECK (
        normal_balance IN ('debit', 'credit')
    )
);

-- Level 4.41: General Ledger
CREATE TABLE IF NOT EXISTS general_ledger (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    transaction_date DATE NOT NULL,
    document_type VARCHAR(50),
    document_id INTEGER,
    description TEXT,
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    running_balance DECIMAL(15,2),
    is_posted BOOLEAN DEFAULT false,
    posted_date TIMESTAMP,
    posted_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    CONSTRAINT fk_ledger_account FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id),
    CONSTRAINT fk_ledger_period FOREIGN KEY (period_id) REFERENCES accounting_periods(id),
    CONSTRAINT chk_ledger_amounts CHECK (
        debit_amount >= 0 AND
        credit_amount >= 0 AND
        (debit_amount = 0 OR credit_amount = 0) -- Can't be both debit and credit
    )
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id SERIAL PRIMARY KEY,
    entry_number VARCHAR(50) NOT NULL UNIQUE,
    period_id INTEGER NOT NULL,
    entry_date DATE NOT NULL,
    entry_type VARCHAR(50) NOT NULL,
    description TEXT,
    reference_number VARCHAR(50),
    status VARCHAR(20) DEFAULT 'draft',
    is_recurring BOOLEAN DEFAULT false,
    is_reversal BOOLEAN DEFAULT false,
    reversed_entry_id INTEGER,
    posted_date TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_journal_period FOREIGN KEY (period_id) REFERENCES accounting_periods(id),
    CONSTRAINT fk_journal_reversal FOREIGN KEY (reversed_entry_id) REFERENCES journal_entries(id),
    CONSTRAINT chk_journal_status CHECK (
        status IN ('draft', 'posted', 'reversed')
    )
);

-- Add indexes for better performance
CREATE INDEX idx_tax_rates_active ON tax_rates(is_active);

CREATE INDEX idx_accounting_periods_dates ON accounting_periods(start_date, end_date);
CREATE INDEX idx_accounting_periods_status ON accounting_periods(status);

CREATE INDEX idx_chart_of_accounts_number ON chart_of_accounts(account_number);
CREATE INDEX idx_chart_of_accounts_type ON chart_of_accounts(account_type);
CREATE INDEX idx_chart_of_accounts_parent ON chart_of_accounts(parent_account_id);
CREATE INDEX idx_chart_of_accounts_active ON chart_of_accounts(is_active);

CREATE INDEX idx_general_ledger_account ON general_ledger(account_id);
CREATE INDEX idx_general_ledger_period ON general_ledger(period_id);
CREATE INDEX idx_general_ledger_date ON general_ledger(transaction_date);
CREATE INDEX idx_general_ledger_document ON general_ledger(document_type, document_id);
CREATE INDEX idx_general_ledger_posted ON general_ledger(is_posted, posted_date);

CREATE INDEX idx_journal_entries_number ON journal_entries(entry_number);
CREATE INDEX idx_journal_entries_period ON journal_entries(period_id);
CREATE INDEX idx_journal_entries_date ON journal_entries(entry_date);
CREATE INDEX idx_journal_entries_status ON journal_entries(status);
CREATE INDEX idx_journal_entries_type ON journal_entries(entry_type);

-- Add comments for documentation
COMMENT ON TABLE tax_rates IS 'Tax rate configurations';
COMMENT ON TABLE accounting_periods IS 'Accounting period definitions';
COMMENT ON TABLE chart_of_accounts IS 'Chart of accounts structure';
COMMENT ON TABLE general_ledger IS 'General ledger transactions';
COMMENT ON TABLE journal_entries IS 'Journal entry header records';

-- Add trigger for general ledger balance update
CREATE OR REPLACE FUNCTION update_account_running_balance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the running balance for the current and all subsequent records
    WITH RECURSIVE running_balance AS (
        -- Get the previous balance
        SELECT 
            id,
            COALESCE((
                SELECT running_balance
                FROM general_ledger
                WHERE account_id = NEW.account_id
                AND transaction_date < NEW.transaction_date
                ORDER BY transaction_date DESC, id DESC
                LIMIT 1
            ), 0) + (NEW.debit_amount - NEW.credit_amount) as balance
        FROM general_ledger
        WHERE id = NEW.id

        UNION ALL

        SELECT 
            gl.id,
            rb.balance + (gl.debit_amount - gl.credit_amount) as balance
        FROM general_ledger gl
        INNER JOIN running_balance rb ON gl.account_id = NEW.account_id
        WHERE gl.transaction_date > NEW.transaction_date
        OR (gl.transaction_date = NEW.transaction_date AND gl.id > NEW.id)
    )
    UPDATE general_ledger gl
    SET running_balance = rb.balance
    FROM running_balance rb
    WHERE gl.id = rb.id;

    -- Update the current balance in chart of accounts
    UPDATE chart_of_accounts
    SET current_balance = (
        SELECT COALESCE(SUM(debit_amount - credit_amount), 0)
        FROM general_ledger
        WHERE account_id = NEW.account_id
        AND is_posted = true
    )
    WHERE id = NEW.account_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ledger_running_balance
    AFTER INSERT OR UPDATE ON general_ledger
    FOR EACH ROW
    EXECUTE FUNCTION update_account_running_balance();

COMMIT;
