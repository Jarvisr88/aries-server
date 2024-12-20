-- Migration Script - Level 4.3 (Inventory and Product Tables)
-- Generated: 2024-12-19
-- Description: Creates inventory and product-related tables

BEGIN;

-- Level 4.8: Product Categories and Groups
CREATE TABLE IF NOT EXISTS product_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_category_id INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_product_category_parent FOREIGN KEY (parent_category_id) REFERENCES product_categories(id)
);

CREATE TABLE IF NOT EXISTS product_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category_id INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_product_group_category FOREIGN KEY (category_id) REFERENCES product_categories(id)
);

-- Level 4.9: Base Products
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category_id INTEGER,
    group_id INTEGER,
    unit_of_measure VARCHAR(20),
    manufacturer VARCHAR(100),
    model_number VARCHAR(50),
    barcode VARCHAR(50),
    is_serialized BOOLEAN DEFAULT false,
    is_lot_tracked BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    reorder_point INTEGER,
    reorder_quantity INTEGER,
    minimum_stock INTEGER,
    maximum_stock INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES product_categories(id),
    CONSTRAINT fk_product_group FOREIGN KEY (group_id) REFERENCES product_groups(id),
    CONSTRAINT chk_product_stock CHECK (
        (reorder_point IS NULL OR reorder_point >= 0) AND
        (reorder_quantity IS NULL OR reorder_quantity >= 0) AND
        (minimum_stock IS NULL OR minimum_stock >= 0) AND
        (maximum_stock IS NULL OR maximum_stock >= minimum_stock)
    )
);

-- Level 4.10: Product Price and History
CREATE TABLE IF NOT EXISTS product_prices (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    price_code VARCHAR(20),
    base_price DECIMAL(10,2),
    retail_price DECIMAL(10,2),
    wholesale_price DECIMAL(10,2),
    insurance_price DECIMAL(10,2),
    effective_date DATE NOT NULL,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_product_price_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT chk_product_price_dates CHECK (effective_date <= end_date OR end_date IS NULL),
    CONSTRAINT chk_product_prices CHECK (
        base_price >= 0 AND
        retail_price >= 0 AND
        wholesale_price >= 0 AND
        insurance_price >= 0
    )
);

CREATE TABLE IF NOT EXISTS product_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    field_name VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(50),
    notes TEXT,
    CONSTRAINT fk_product_history_product FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Level 4.11: Kit Management
CREATE TABLE IF NOT EXISTS kits (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    kit_type VARCHAR(50),
    product_group_id INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_kit_product_group FOREIGN KEY (product_group_id) REFERENCES product_groups(id)
);

CREATE TABLE IF NOT EXISTS kit_details (
    id SERIAL PRIMARY KEY,
    kit_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    is_required BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_kit_detail_kit FOREIGN KEY (kit_id) REFERENCES kits(id),
    CONSTRAINT fk_kit_detail_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT chk_kit_detail_quantity CHECK (quantity > 0)
);

-- Level 4.12: Inventory Transactions
CREATE TABLE IF NOT EXISTS inventory_transaction_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    affects_quantity VARCHAR(10) CHECK (affects_quantity IN ('increase', 'decrease', 'none')),
    requires_approval BOOLEAN DEFAULT false,
    is_system_type BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

-- Add indexes for better performance
CREATE INDEX idx_product_categories_parent ON product_categories(parent_category_id);
CREATE INDEX idx_product_categories_name ON product_categories(name);

CREATE INDEX idx_product_groups_category ON product_groups(category_id);
CREATE INDEX idx_product_groups_name ON product_groups(name);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_group ON products(group_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_manufacturer ON products(manufacturer);
CREATE INDEX idx_products_barcode ON products(barcode);

CREATE INDEX idx_product_prices_product ON product_prices(product_id);
CREATE INDEX idx_product_prices_dates ON product_prices(effective_date, end_date);
CREATE INDEX idx_product_prices_code ON product_prices(price_code);

CREATE INDEX idx_product_history_product ON product_history(product_id);
CREATE INDEX idx_product_history_dates ON product_history(change_date);
CREATE INDEX idx_product_history_type ON product_history(change_type);

CREATE INDEX idx_kits_group ON kits(product_group_id);
CREATE INDEX idx_kits_name ON kits(name);
CREATE INDEX idx_kits_type ON kits(kit_type);

CREATE INDEX idx_kit_details_kit ON kit_details(kit_id);
CREATE INDEX idx_kit_details_product ON kit_details(product_id);

CREATE INDEX idx_inventory_transaction_types_name ON inventory_transaction_types(name);

-- Add comments for documentation
COMMENT ON TABLE product_categories IS 'Hierarchical categories for products';
COMMENT ON TABLE product_groups IS 'Product groupings within categories';
COMMENT ON TABLE products IS 'Base product information';
COMMENT ON TABLE product_prices IS 'Product pricing history with different price types';
COMMENT ON TABLE product_history IS 'Audit trail of product changes';
COMMENT ON TABLE kits IS 'Product kits or bundles configuration';
COMMENT ON TABLE kit_details IS 'Individual products within kits';
COMMENT ON TABLE inventory_transaction_types IS 'Types of inventory transactions';

COMMIT;
