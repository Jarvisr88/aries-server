-- Migration Script - Level 4.25 (Email and File Management)
-- Generated: 2024-12-19
-- Description: Creates tables for email templates, file attachments, and notifications

DO $$ 
BEGIN

-- Drop existing tables if they exist
DROP TABLE IF EXISTS notification_recipients CASCADE;
DROP TABLE IF EXISTS notification_queue CASCADE;
DROP TABLE IF EXISTS email_attachments CASCADE;
DROP TABLE IF EXISTS email_templates CASCADE;
DROP TABLE IF EXISTS file_attachments CASCADE;
DROP TABLE IF EXISTS file_categories CASCADE;

-- Create file management tables
CREATE TABLE IF NOT EXISTS file_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER,
    allowed_extensions TEXT[],
    max_file_size INTEGER,
    retention_days INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_file_category_parent FOREIGN KEY (parent_id) REFERENCES file_categories(id),
    CONSTRAINT uq_file_category_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS file_attachments (
    id SERIAL PRIMARY KEY,
    category_id INTEGER,
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(100),
    mime_type VARCHAR(100),
    file_size BIGINT,
    checksum VARCHAR(64),
    entity_type VARCHAR(50),
    entity_id INTEGER,
    is_public BOOLEAN DEFAULT false,
    expiry_date TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_file_category FOREIGN KEY (category_id) REFERENCES file_categories(id)
);

-- Create email template tables
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    template_code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    subject VARCHAR(200) NOT NULL,
    body_html TEXT,
    body_text TEXT,
    variables JSONB,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_email_template_code UNIQUE (template_code)
);

CREATE TABLE IF NOT EXISTS email_attachments (
    id SERIAL PRIMARY KEY,
    email_id INTEGER NOT NULL,
    file_attachment_id INTEGER NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_email_attachment_file FOREIGN KEY (file_attachment_id) REFERENCES file_attachments(id)
);

-- Create notification tables
CREATE TABLE IF NOT EXISTS notification_queue (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL,
    template_id INTEGER,
    subject VARCHAR(200),
    message TEXT,
    priority INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_notification_template FOREIGN KEY (template_id) REFERENCES email_templates(id),
    CONSTRAINT chk_notification_status CHECK (
        status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')
    )
);

CREATE TABLE IF NOT EXISTS notification_recipients (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER NOT NULL,
    recipient_type VARCHAR(20) NOT NULL,
    recipient_address VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notification_queue FOREIGN KEY (notification_id) REFERENCES notification_queue(id),
    CONSTRAINT chk_recipient_type CHECK (
        recipient_type IN ('to', 'cc', 'bcc')
    ),
    CONSTRAINT chk_recipient_status CHECK (
        status IN ('pending', 'sent', 'failed', 'bounced')
    )
);

-- Add indexes for better performance
CREATE INDEX idx_file_categories_parent ON file_categories(parent_id);
CREATE INDEX idx_file_categories_name ON file_categories(name);

CREATE INDEX idx_file_attachments_category ON file_attachments(category_id);
CREATE INDEX idx_file_attachments_entity ON file_attachments(entity_type, entity_id);
CREATE INDEX idx_file_attachments_public ON file_attachments(is_public);
CREATE INDEX idx_file_attachments_expiry ON file_attachments(expiry_date);

CREATE INDEX idx_email_templates_code ON email_templates(template_code);
CREATE INDEX idx_email_templates_active ON email_templates(is_active);

CREATE INDEX idx_email_attachments_email ON email_attachments(email_id);
CREATE INDEX idx_email_attachments_file ON email_attachments(file_attachment_id);

CREATE INDEX idx_notification_queue_type ON notification_queue(notification_type);
CREATE INDEX idx_notification_queue_status ON notification_queue(status);
CREATE INDEX idx_notification_queue_schedule ON notification_queue(scheduled_at);
CREATE INDEX idx_notification_queue_priority ON notification_queue(priority);

CREATE INDEX idx_notification_recipients_notification ON notification_recipients(notification_id);
CREATE INDEX idx_notification_recipients_status ON notification_recipients(status);
CREATE INDEX idx_notification_recipients_type ON notification_recipients(recipient_type);

EXCEPTION WHEN OTHERS THEN
    -- Roll back the transaction on error
    RAISE NOTICE 'Error occurred: %', SQLERRM;
    RAISE EXCEPTION 'Transaction aborted';
END;
$$ LANGUAGE plpgsql;
