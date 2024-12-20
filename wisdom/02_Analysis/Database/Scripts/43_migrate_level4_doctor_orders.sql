-- Migration Script - Level 4.27 (Doctor Orders and Medical Records)
-- Generated: 2024-12-19
-- Description: Creates tables for doctor orders, prescriptions, and medical records

DO $$ 
BEGIN

-- Drop existing tables if they exist
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS order_fulfillment CASCADE;
DROP TABLE IF EXISTS order_history CASCADE;
DROP TABLE IF EXISTS doctor_orders CASCADE;
DROP TABLE IF EXISTS prescription_refills CASCADE;
DROP TABLE IF EXISTS prescriptions CASCADE;

-- Create doctor orders tables
CREATE TABLE IF NOT EXISTS doctor_orders (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    order_type VARCHAR(50) NOT NULL,
    order_date TIMESTAMP NOT NULL,
    start_date DATE,
    end_date DATE,
    diagnosis_codes JSONB,
    instructions TEXT,
    frequency VARCHAR(50),
    duration VARCHAR(50),
    quantity INTEGER,
    refills INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'routine',
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_doctor_order_patient FOREIGN KEY (patient_id) REFERENCES patients(id),
    CONSTRAINT fk_doctor_order_doctor FOREIGN KEY (doctor_id) REFERENCES doctors(id),
    CONSTRAINT chk_order_status CHECK (
        status IN ('pending', 'approved', 'completed', 'cancelled', 'expired')
    ),
    CONSTRAINT chk_order_priority CHECK (
        priority IN ('stat', 'urgent', 'routine', 'low')
    ),
    CONSTRAINT chk_order_dates CHECK (
        start_date <= end_date OR end_date IS NULL
    )
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER,
    item_type VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2),
    instructions TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES doctor_orders(id),
    CONSTRAINT fk_order_item_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT chk_item_status CHECK (
        status IN ('pending', 'processing', 'completed', 'cancelled')
    )
);

CREATE TABLE IF NOT EXISTS order_fulfillment (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    fulfilled_by INTEGER,
    fulfilled_date TIMESTAMP NOT NULL,
    quantity_fulfilled INTEGER NOT NULL,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fulfillment_order FOREIGN KEY (order_id) REFERENCES doctor_orders(id),
    CONSTRAINT fk_fulfillment_employee FOREIGN KEY (fulfilled_by) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS order_history (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    change_date TIMESTAMP NOT NULL,
    changed_by VARCHAR(50),
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_history_order FOREIGN KEY (order_id) REFERENCES doctor_orders(id)
);

-- Create prescription tables
CREATE TABLE IF NOT EXISTS prescriptions (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    medication_name VARCHAR(200) NOT NULL,
    strength VARCHAR(50),
    form VARCHAR(50),
    sig TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    refills INTEGER DEFAULT 0,
    dispense_as_written BOOLEAN DEFAULT false,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_prescription_patient FOREIGN KEY (patient_id) REFERENCES patients(id),
    CONSTRAINT fk_prescription_doctor FOREIGN KEY (doctor_id) REFERENCES doctors(id),
    CONSTRAINT chk_prescription_status CHECK (
        status IN ('active', 'completed', 'discontinued', 'expired')
    )
);

CREATE TABLE IF NOT EXISTS prescription_refills (
    id SERIAL PRIMARY KEY,
    prescription_id INTEGER NOT NULL,
    refill_date DATE NOT NULL,
    quantity INTEGER NOT NULL,
    pharmacy_name VARCHAR(200),
    pharmacy_phone VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_refill_prescription FOREIGN KEY (prescription_id) REFERENCES prescriptions(id),
    CONSTRAINT chk_refill_status CHECK (
        status IN ('pending', 'approved', 'denied', 'filled')
    )
);

-- Add indexes for better performance
CREATE INDEX idx_doctor_orders_patient ON doctor_orders(patient_id);
CREATE INDEX idx_doctor_orders_doctor ON doctor_orders(doctor_id);
CREATE INDEX idx_doctor_orders_type ON doctor_orders(order_type);
CREATE INDEX idx_doctor_orders_dates ON doctor_orders(order_date, start_date, end_date);
CREATE INDEX idx_doctor_orders_status ON doctor_orders(status);
CREATE INDEX idx_doctor_orders_priority ON doctor_orders(priority);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_order_items_status ON order_items(status);

CREATE INDEX idx_order_fulfillment_order ON order_fulfillment(order_id);
CREATE INDEX idx_order_fulfillment_employee ON order_fulfillment(fulfilled_by);
CREATE INDEX idx_order_fulfillment_date ON order_fulfillment(fulfilled_date);

CREATE INDEX idx_order_history_order ON order_history(order_id);
CREATE INDEX idx_order_history_status ON order_history(status);
CREATE INDEX idx_order_history_date ON order_history(change_date);

CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX idx_prescriptions_doctor ON prescriptions(doctor_id);
CREATE INDEX idx_prescriptions_dates ON prescriptions(start_date, end_date);
CREATE INDEX idx_prescriptions_status ON prescriptions(status);

CREATE INDEX idx_prescription_refills_prescription ON prescription_refills(prescription_id);
CREATE INDEX idx_prescription_refills_date ON prescription_refills(refill_date);
CREATE INDEX idx_prescription_refills_status ON prescription_refills(status);

EXCEPTION WHEN OTHERS THEN
    -- Roll back the transaction on error
    RAISE NOTICE 'Error occurred: %', SQLERRM;
    RAISE EXCEPTION 'Transaction aborted';
END;
$$ LANGUAGE plpgsql;
