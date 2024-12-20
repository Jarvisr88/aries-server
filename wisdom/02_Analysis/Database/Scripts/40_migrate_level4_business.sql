-- Migration Script - Level 4.24 (Business and Company Tables)
-- Generated: 2024-12-19
-- Description: Creates tables for company types, customer management, and business operations

DO $$ 
BEGIN

-- Drop existing tables if they exist
DROP TABLE IF EXISTS kit_items CASCADE;
DROP TABLE IF EXISTS kit_templates CASCADE;
DROP TABLE IF EXISTS product_prices CASCADE;
DROP TABLE IF EXISTS product_history CASCADE;
DROP TABLE IF EXISTS product_types CASCADE;
DROP TABLE IF EXISTS product_groups CASCADE;
DROP TABLE IF EXISTS product_categories CASCADE;
DROP TABLE IF EXISTS price_history CASCADE;
DROP TABLE IF EXISTS price_codes CASCADE;
DROP TABLE IF EXISTS vendors CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS legal_representatives CASCADE;
DROP TABLE IF EXISTS customer_types CASCADE;
DROP TABLE IF EXISTS customer_classes CASCADE;
DROP TABLE IF EXISTS company_types CASCADE;

-- Level 4.71: Company and Customer Management
CREATE TABLE IF NOT EXISTS company_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER,
    display_order INTEGER,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_company_type_parent FOREIGN KEY (parent_id) REFERENCES company_types(id),
    CONSTRAINT uq_company_type_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS customer_classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    priority_level INTEGER,
    discount_rate DECIMAL(5,2),
    credit_limit DECIMAL(12,2),
    payment_terms VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_customer_class_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS customer_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    class_id INTEGER,
    billing_cycle VARCHAR(50),
    payment_methods VARCHAR[],
    requirements JSONB,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_customer_type_class FOREIGN KEY (class_id) REFERENCES customer_classes(id),
    CONSTRAINT uq_customer_type_name UNIQUE (name)
);

-- Level 4.72: Location and Legal Management
CREATE TABLE IF NOT EXISTS legal_representatives (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    relationship VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(255),
    address_id INTEGER,
    documentation_path TEXT,
    valid_from DATE NOT NULL,
    valid_until DATE,
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_legal_rep_address FOREIGN KEY (address_id) REFERENCES addresses(id),
    CONSTRAINT chk_legal_rep_dates CHECK (
        valid_from <= valid_until OR valid_until IS NULL
    )
);

CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    address_id INTEGER,
    parent_id INTEGER,
    manager_id INTEGER,
    phone VARCHAR(20),
    email VARCHAR(255),
    operating_hours JSONB,
    capacity INTEGER,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_location_address FOREIGN KEY (address_id) REFERENCES addresses(id),
    CONSTRAINT fk_location_parent FOREIGN KEY (parent_id) REFERENCES locations(id),
    CONSTRAINT fk_location_manager FOREIGN KEY (manager_id) REFERENCES employees(id),
    CONSTRAINT uq_location_name UNIQUE (name),
    CONSTRAINT chk_location_type CHECK (
        type IN ('warehouse', 'office', 'retail', 'distribution', 'storage')
    )
);

-- Level 4.73: Vendor Management
CREATE TABLE IF NOT EXISTS vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    company_type_id INTEGER,
    tax_id VARCHAR(50),
    contact_name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    address_id INTEGER,
    payment_terms VARCHAR(100),
    credit_limit DECIMAL(12,2),
    rating INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_vendor_company_type FOREIGN KEY (company_type_id) REFERENCES company_types(id),
    CONSTRAINT fk_vendor_address FOREIGN KEY (address_id) REFERENCES addresses(id),
    CONSTRAINT uq_vendor_name UNIQUE (name),
    CONSTRAINT chk_vendor_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT chk_vendor_status CHECK (
        status IN ('active', 'inactive', 'pending', 'suspended')
    )
);

-- Level 4.74: Product and Price Management
CREATE TABLE IF NOT EXISTS price_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    calculation_method VARCHAR(50),
    markup_rate DECIMAL(5,2),
    discount_rate DECIMAL(5,2),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_price_code UNIQUE (code),
    CONSTRAINT chk_calculation_method CHECK (
        calculation_method IN ('fixed', 'markup', 'discount', 'custom')
    )
);

CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    price_code_id INTEGER,
    old_price DECIMAL(12,2),
    new_price DECIMAL(12,2),
    change_reason TEXT,
    effective_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    CONSTRAINT fk_price_history_code FOREIGN KEY (price_code_id) REFERENCES price_codes(id),
    CONSTRAINT chk_price_dates CHECK (
        effective_date <= end_date OR end_date IS NULL
    )
);

CREATE TABLE IF NOT EXISTS product_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER,
    display_order INTEGER,
    image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_product_category_parent FOREIGN KEY (parent_id) REFERENCES product_categories(id),
    CONSTRAINT uq_product_category_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS product_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category_id INTEGER,
    display_order INTEGER,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_product_group_category FOREIGN KEY (category_id) REFERENCES product_categories(id),
    CONSTRAINT uq_product_group_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS product_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    group_id INTEGER,
    attributes JSONB,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_product_type_group FOREIGN KEY (group_id) REFERENCES product_groups(id),
    CONSTRAINT uq_product_type_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS product_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_type VARCHAR(20),
    change_reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    CONSTRAINT fk_product_history_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT chk_change_type CHECK (
        change_type IN ('create', 'update', 'delete', 'restore')
    )
);

CREATE TABLE IF NOT EXISTS product_prices (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    price_code_id INTEGER NOT NULL,
    base_price DECIMAL(12,2) NOT NULL,
    min_price DECIMAL(12,2),
    max_price DECIMAL(12,2),
    effective_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_product_price_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT fk_product_price_code FOREIGN KEY (price_code_id) REFERENCES price_codes(id),
    CONSTRAINT uq_product_price UNIQUE (product_id, price_code_id, effective_date),
    CONSTRAINT chk_product_price_dates CHECK (
        effective_date <= end_date OR end_date IS NULL
    ),
    CONSTRAINT chk_product_price_range CHECK (
        min_price <= base_price AND
        (max_price IS NULL OR base_price <= max_price)
    )
);

-- Level 4.75: Kit Management
CREATE TABLE IF NOT EXISTS kit_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    product_type_id INTEGER,
    version VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_kit_template_type FOREIGN KEY (product_type_id) REFERENCES product_types(id),
    CONSTRAINT uq_kit_template_name UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS kit_items (
    id SERIAL PRIMARY KEY,
    kit_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    is_required BOOLEAN DEFAULT true,
    display_order INTEGER,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_kit_item_kit FOREIGN KEY (kit_id) REFERENCES kit_templates(id),
    CONSTRAINT fk_kit_item_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT uq_kit_item UNIQUE (kit_id, product_id)
);

-- Add indexes for better performance
CREATE INDEX idx_company_types_parent ON company_types(parent_id);
CREATE INDEX idx_company_types_active ON company_types(is_active);

CREATE INDEX idx_customer_classes_priority ON customer_classes(priority_level);
CREATE INDEX idx_customer_classes_active ON customer_classes(is_active);

CREATE INDEX idx_customer_types_class ON customer_types(class_id);
CREATE INDEX idx_customer_types_active ON customer_types(is_active);

CREATE INDEX idx_legal_reps_entity ON legal_representatives(entity_type, entity_id);
CREATE INDEX idx_legal_reps_dates ON legal_representatives(valid_from, valid_until);
CREATE INDEX idx_legal_reps_active ON legal_representatives(is_active);

CREATE INDEX idx_locations_type ON locations(type);
CREATE INDEX idx_locations_parent ON locations(parent_id);
CREATE INDEX idx_locations_manager ON locations(manager_id);
CREATE INDEX idx_locations_active ON locations(is_active);

CREATE INDEX idx_vendors_type ON vendors(company_type_id);
CREATE INDEX idx_vendors_status ON vendors(status);

CREATE INDEX idx_price_codes_active ON price_codes(is_active);

CREATE INDEX idx_price_history_entity ON price_history(entity_type, entity_id);
CREATE INDEX idx_price_history_dates ON price_history(effective_date, end_date);

CREATE INDEX idx_product_categories_parent ON product_categories(parent_id);
CREATE INDEX idx_product_categories_active ON product_categories(is_active);

CREATE INDEX idx_product_groups_category ON product_groups(category_id);
CREATE INDEX idx_product_groups_active ON product_groups(is_active);

CREATE INDEX idx_product_types_group ON product_types(group_id);
CREATE INDEX idx_product_types_active ON product_types(is_active);

CREATE INDEX idx_product_history_product ON product_history(product_id);
CREATE INDEX idx_product_history_field ON product_history(field_name);
CREATE INDEX idx_product_history_change ON product_history(change_type);

CREATE INDEX idx_product_prices_product ON product_prices(product_id);
CREATE INDEX idx_product_prices_code ON product_prices(price_code_id);
CREATE INDEX idx_product_prices_dates ON product_prices(effective_date, end_date);
CREATE INDEX idx_product_prices_active ON product_prices(is_active);

CREATE INDEX idx_kit_templates_type ON kit_templates(product_type_id);
CREATE INDEX idx_kit_templates_active ON kit_templates(is_active);

CREATE INDEX idx_kit_items_kit ON kit_items(kit_id);
CREATE INDEX idx_kit_items_product ON kit_items(product_id);
CREATE INDEX idx_kit_items_order ON kit_items(display_order);

-- Add comments for documentation
COMMENT ON TABLE company_types IS 'Company classification types';
COMMENT ON TABLE customer_classes IS 'Customer classification and priority levels';
COMMENT ON TABLE customer_types IS 'Customer type definitions';
COMMENT ON TABLE legal_representatives IS 'Legal representative information';
COMMENT ON TABLE locations IS 'Physical location and facility management';
COMMENT ON TABLE vendors IS 'Vendor and supplier management';
COMMENT ON TABLE price_codes IS 'Price code and calculation methods';
COMMENT ON TABLE price_history IS 'Historical price changes';
COMMENT ON TABLE product_categories IS 'Product category hierarchy';
COMMENT ON TABLE product_groups IS 'Product grouping definitions';
COMMENT ON TABLE product_types IS 'Product type classifications';
COMMENT ON TABLE product_history IS 'Product change history';
COMMENT ON TABLE product_prices IS 'Product pricing information';
COMMENT ON TABLE kit_templates IS 'Product kit templates';
COMMENT ON TABLE kit_items IS 'Items included in product kits';

EXCEPTION WHEN OTHERS THEN
    -- Roll back the transaction on error
    RAISE NOTICE 'Error occurred: %', SQLERRM;
    RAISE EXCEPTION 'Transaction aborted';
END;
$$ LANGUAGE plpgsql;
