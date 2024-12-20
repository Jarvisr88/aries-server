-- Migration Script - Level 4.21 (Communication Templates)
-- Generated: 2024-12-19
-- Description: Creates communication templates and messaging tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS message_attachments CASCADE;
DROP TABLE IF EXISTS message_recipients CASCADE;
DROP TABLE IF EXISTS message_queue CASCADE;
DROP TABLE IF EXISTS template_versions CASCADE;
DROP TABLE IF EXISTS communication_templates CASCADE;
DROP TABLE IF EXISTS template_categories CASCADE;

-- Level 4.63: Template Management
CREATE TABLE IF NOT EXISTS template_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER,
    display_order INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_template_category_parent FOREIGN KEY (parent_id) REFERENCES template_categories(id),
    CONSTRAINT uq_template_category_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS communication_templates (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL,
    subject_template TEXT,
    body_template TEXT NOT NULL,
    format VARCHAR(20) DEFAULT 'text',
    variables JSONB,
    metadata JSONB,
    is_system_template BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_communication_template_category FOREIGN KEY (category_id) REFERENCES template_categories(id),
    CONSTRAINT uq_communication_template_name UNIQUE (name),
    CONSTRAINT chk_template_type CHECK (
        template_type IN ('email', 'sms', 'push', 'letter', 'report')
    ),
    CONSTRAINT chk_template_format CHECK (
        format IN ('text', 'html', 'markdown')
    )
);

CREATE TABLE IF NOT EXISTS template_versions (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    subject_template TEXT,
    body_template TEXT NOT NULL,
    variables JSONB,
    metadata JSONB,
    is_active BOOLEAN DEFAULT false,
    published_at TIMESTAMP,
    published_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    CONSTRAINT fk_template_version_template FOREIGN KEY (template_id) REFERENCES communication_templates(id),
    CONSTRAINT uq_template_version UNIQUE (template_id, version_number)
);

-- Level 4.64: Message Queue
CREATE TABLE IF NOT EXISTS message_queue (
    id SERIAL PRIMARY KEY,
    template_id INTEGER,
    template_version_id INTEGER,
    message_type VARCHAR(50) NOT NULL,
    subject TEXT,
    body TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    scheduled_time TIMESTAMP,
    processed_time TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_message_template FOREIGN KEY (template_id) REFERENCES communication_templates(id),
    CONSTRAINT fk_message_template_version FOREIGN KEY (template_version_id) REFERENCES template_versions(id),
    CONSTRAINT chk_message_type CHECK (
        message_type IN ('email', 'sms', 'push', 'letter')
    ),
    CONSTRAINT chk_message_status CHECK (
        status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')
    )
);

CREATE TABLE IF NOT EXISTS message_recipients (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL,
    recipient_type VARCHAR(20) NOT NULL,
    recipient_address TEXT NOT NULL,
    recipient_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    sent_time TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_message_recipient_message FOREIGN KEY (message_id) REFERENCES message_queue(id),
    CONSTRAINT chk_recipient_type CHECK (
        recipient_type IN ('to', 'cc', 'bcc')
    ),
    CONSTRAINT chk_recipient_status CHECK (
        status IN ('pending', 'sent', 'failed', 'bounced')
    )
);

CREATE TABLE IF NOT EXISTS message_attachments (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    file_size INTEGER,
    content_type VARCHAR(100),
    storage_path TEXT,
    is_inline BOOLEAN DEFAULT false,
    content_id VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_message_attachment_message FOREIGN KEY (message_id) REFERENCES message_queue(id)
);

-- Add indexes for better performance
CREATE INDEX idx_template_categories_parent ON template_categories(parent_id);
CREATE INDEX idx_template_categories_active ON template_categories(is_active);

CREATE INDEX idx_communication_templates_category ON communication_templates(category_id);
CREATE INDEX idx_communication_templates_type ON communication_templates(template_type);
CREATE INDEX idx_communication_templates_active ON communication_templates(is_active);
CREATE INDEX idx_communication_templates_system ON communication_templates(is_system_template);

CREATE INDEX idx_template_versions_template ON template_versions(template_id);
CREATE INDEX idx_template_versions_active ON template_versions(is_active);
CREATE INDEX idx_template_versions_published ON template_versions(published_at);

CREATE INDEX idx_message_queue_template ON message_queue(template_id);
CREATE INDEX idx_message_queue_version ON message_queue(template_version_id);
CREATE INDEX idx_message_queue_type ON message_queue(message_type);
CREATE INDEX idx_message_queue_status ON message_queue(status);
CREATE INDEX idx_message_queue_scheduled ON message_queue(scheduled_time);
CREATE INDEX idx_message_queue_processed ON message_queue(processed_time);

CREATE INDEX idx_message_recipients_message ON message_recipients(message_id);
CREATE INDEX idx_message_recipients_type ON message_recipients(recipient_type);
CREATE INDEX idx_message_recipients_status ON message_recipients(status);
CREATE INDEX idx_message_recipients_address ON message_recipients(recipient_address);

CREATE INDEX idx_message_attachments_message ON message_attachments(message_id);
CREATE INDEX idx_message_attachments_type ON message_attachments(file_type);

-- Add comments for documentation
COMMENT ON TABLE template_categories IS 'Communication template categories';
COMMENT ON TABLE communication_templates IS 'Communication template definitions';
COMMENT ON TABLE template_versions IS 'Version history for communication templates';
COMMENT ON TABLE message_queue IS 'Message processing queue';
COMMENT ON TABLE message_recipients IS 'Message recipient details';
COMMENT ON TABLE message_attachments IS 'Message attachment information';

COMMIT;
