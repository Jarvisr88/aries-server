-- Migration Script - Level 4.12 (Order Management)
-- Generated: 2024-12-19
-- Description: Creates order processing and fulfillment tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS order_fulfillments CASCADE;
DROP TABLE IF EXISTS order_status_history CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS order_types CASCADE;

-- Level 4.32: Order Configuration
CREATE TABLE IF NOT EXISTS order_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    workflow_type VARCHAR(50),
    requires_approval BOOLEAN DEFAULT false,
    auto_fulfill BOOLEAN DEFAULT false,
    settings JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_order_type_name UNIQUE (name)
);

-- Level 4.33: Order Management
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    order_type_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    order_date TIMESTAMP NOT NULL,
    due_date TIMESTAMP,
    shipping_method_id INTEGER,
    shipping_address_id INTEGER,
    billing_address_id INTEGER,
    subtotal DECIMAL(10,2) NOT NULL,
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) NOT NULL,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_order_type FOREIGN KEY (order_type_id) REFERENCES order_types(id),
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_order_company FOREIGN KEY (company_id) REFERENCES companies(id),
    CONSTRAINT fk_order_shipping_method FOREIGN KEY (shipping_method_id) REFERENCES shipping_methods(id),
    CONSTRAINT chk_order_amounts CHECK (
        subtotal >= 0 AND
        shipping_cost >= 0 AND
        tax_amount >= 0 AND
        discount_amount >= 0 AND
        total_amount >= 0
    ),
    CONSTRAINT chk_order_dates CHECK (
        order_date <= due_date OR due_date IS NULL
    )
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    tax_percent DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    line_total DECIMAL(10,2) NOT NULL,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_order_item_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT chk_order_item_quantity CHECK (quantity > 0),
    CONSTRAINT chk_order_item_amounts CHECK (
        unit_price >= 0 AND
        discount_percent >= 0 AND
        discount_percent <= 100 AND
        discount_amount >= 0 AND
        tax_percent >= 0 AND
        tax_percent <= 100 AND
        tax_amount >= 0 AND
        line_total >= 0
    )
);

-- Level 4.34: Order Processing
CREATE TABLE IF NOT EXISTS order_status_history (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    CONSTRAINT fk_order_status_order FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS order_fulfillments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    fulfillment_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_package_id INTEGER,
    tracking_number VARCHAR(100),
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_order_fulfillment_order FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_order_fulfillment_package FOREIGN KEY (shipping_package_id) REFERENCES shipping_packages(id)
);

-- Add indexes for better performance
CREATE INDEX idx_order_types_active ON order_types(is_active);
CREATE INDEX idx_order_types_workflow ON order_types(workflow_type);

CREATE INDEX idx_orders_number ON orders(order_number);
CREATE INDEX idx_orders_type ON orders(order_type_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_company ON orders(company_id);
CREATE INDEX idx_orders_dates ON orders(order_date, due_date);
CREATE INDEX idx_orders_status ON orders(status);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

CREATE INDEX idx_order_status_history_order ON order_status_history(order_id);
CREATE INDEX idx_order_status_history_status ON order_status_history(status);
CREATE INDEX idx_order_status_history_date ON order_status_history(created_at);

CREATE INDEX idx_order_fulfillments_order ON order_fulfillments(order_id);
CREATE INDEX idx_order_fulfillments_package ON order_fulfillments(shipping_package_id);
CREATE INDEX idx_order_fulfillments_date ON order_fulfillments(fulfillment_date);
CREATE INDEX idx_order_fulfillments_status ON order_fulfillments(status);

-- Add comments for documentation
COMMENT ON TABLE order_types IS 'Order type configurations';
COMMENT ON TABLE orders IS 'Main order management table';
COMMENT ON TABLE order_items IS 'Order line items';
COMMENT ON TABLE order_status_history IS 'Order status change history';
COMMENT ON TABLE order_fulfillments IS 'Order fulfillment tracking';

-- Add trigger for order status history
CREATE OR REPLACE FUNCTION track_order_status_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE' AND NEW.status <> OLD.status) OR TG_OP = 'INSERT' THEN
        INSERT INTO order_status_history (
            order_id,
            status,
            created_by
        ) VALUES (
            NEW.id,
            NEW.status,
            NEW.updated_by
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER track_order_status_changes
    AFTER INSERT OR UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION track_order_status_changes();

COMMIT;
