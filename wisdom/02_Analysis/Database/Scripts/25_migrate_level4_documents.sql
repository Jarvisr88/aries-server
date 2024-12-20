-- Migration Script - Level 4.9 (Document Management)
-- Generated: 2024-12-19
-- Description: Creates document management, templates, and versioning tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS document_versions CASCADE;
DROP TABLE IF EXISTS document_shares CASCADE;
DROP TABLE IF EXISTS document_tags CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS document_templates CASCADE;
DROP TABLE IF EXISTS document_categories CASCADE;

-- Level 4.24: Document Categories and Templates
CREATE TABLE IF NOT EXISTS document_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_category_id INTEGER,
    is_system_category BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_document_category_name UNIQUE (name),
    CONSTRAINT fk_document_category_parent FOREIGN KEY (parent_category_id) REFERENCES document_categories(id)
);

CREATE TABLE IF NOT EXISTS document_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category_id INTEGER,
    content TEXT,
    file_extension VARCHAR(10),
    variables JSONB,
    is_system_template BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_document_template_name UNIQUE (name),
    CONSTRAINT fk_document_template_category FOREIGN KEY (category_id) REFERENCES document_categories(id)
);

-- Level 4.25: Document Management
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INTEGER,
    template_id INTEGER,
    file_path VARCHAR(500),
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(10),
    file_size BIGINT,
    mime_type VARCHAR(100),
    status VARCHAR(20) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    is_template_generated BOOLEAN DEFAULT false,
    is_locked BOOLEAN DEFAULT false,
    locked_by INTEGER,
    locked_at TIMESTAMP,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_document_category FOREIGN KEY (category_id) REFERENCES document_categories(id),
    CONSTRAINT fk_document_template FOREIGN KEY (template_id) REFERENCES document_templates(id),
    CONSTRAINT fk_document_locked_by FOREIGN KEY (locked_by) REFERENCES users(id),
    CONSTRAINT chk_document_file_size CHECK (file_size >= 0),
    CONSTRAINT chk_document_version CHECK (version > 0),
    CONSTRAINT chk_document_status CHECK (status IN ('draft', 'review', 'approved', 'archived'))
);

CREATE TABLE IF NOT EXISTS document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    change_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    CONSTRAINT fk_document_version_document FOREIGN KEY (document_id) REFERENCES documents(id),
    CONSTRAINT chk_document_version_size CHECK (file_size >= 0),
    CONSTRAINT uq_document_version UNIQUE (document_id, version)
);

CREATE TABLE IF NOT EXISTS document_shares (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    shared_with_type VARCHAR(50) NOT NULL,
    shared_with_id INTEGER NOT NULL,
    permission_level VARCHAR(20) DEFAULT 'read',
    expiry_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_document_share_document FOREIGN KEY (document_id) REFERENCES documents(id),
    CONSTRAINT chk_document_share_permission CHECK (
        permission_level IN ('read', 'write', 'admin')
    )
);

CREATE TABLE IF NOT EXISTS document_tags (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    tag_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    CONSTRAINT fk_document_tag_document FOREIGN KEY (document_id) REFERENCES documents(id),
    CONSTRAINT uq_document_tag UNIQUE (document_id, tag_name)
);

-- Add indexes for better performance
CREATE INDEX idx_document_categories_parent ON document_categories(parent_category_id);
CREATE INDEX idx_document_categories_name ON document_categories(name);

CREATE INDEX idx_document_templates_category ON document_templates(category_id);
CREATE INDEX idx_document_templates_name ON document_templates(name);

CREATE INDEX idx_documents_category ON documents(category_id);
CREATE INDEX idx_documents_template ON documents(template_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_entity ON documents(entity_type, entity_id);
CREATE INDEX idx_documents_locked ON documents(locked_by, locked_at);

CREATE INDEX idx_document_versions_document ON document_versions(document_id);
CREATE INDEX idx_document_versions_version ON document_versions(version);

CREATE INDEX idx_document_shares_document ON document_shares(document_id);
CREATE INDEX idx_document_shares_shared ON document_shares(shared_with_type, shared_with_id);
CREATE INDEX idx_document_shares_expiry ON document_shares(expiry_date);

CREATE INDEX idx_document_tags_document ON document_tags(document_id);
CREATE INDEX idx_document_tags_name ON document_tags(tag_name);

-- Add comments for documentation
COMMENT ON TABLE document_categories IS 'Hierarchical categories for document organization';
COMMENT ON TABLE document_templates IS 'Document templates with variable support';
COMMENT ON TABLE documents IS 'Main document management table';
COMMENT ON TABLE document_versions IS 'Document version history';
COMMENT ON TABLE document_shares IS 'Document sharing and permissions';
COMMENT ON TABLE document_tags IS 'Document tagging system';

-- Add trigger for document locking
CREATE OR REPLACE FUNCTION update_document_lock()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_locked = true AND OLD.is_locked = false THEN
        NEW.locked_at = CURRENT_TIMESTAMP;
    END IF;
    IF NEW.is_locked = false AND OLD.is_locked = true THEN
        NEW.locked_at = NULL;
        NEW.locked_by = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_document_lock_timestamp
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_document_lock();

COMMIT;
