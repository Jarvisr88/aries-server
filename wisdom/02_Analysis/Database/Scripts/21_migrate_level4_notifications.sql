-- Migration Script - Level 4.5 (Notifications and Communications)
-- Generated: 2024-12-19
-- Description: Creates notification, email template, and file management tables

BEGIN;

-- Level 4.13: Users table (if not exists)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

-- Level 4.14: Email Templates
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    body_text TEXT NOT NULL,
    body_html TEXT,
    template_type VARCHAR(50),
    variables JSONB,
    is_system_template BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_email_template_name UNIQUE (name)
);

-- Level 4.14: Notification Management
CREATE TABLE IF NOT EXISTS notification_queue (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL,
    recipient_type VARCHAR(50) NOT NULL,
    recipient_id INTEGER NOT NULL,
    subject VARCHAR(200),
    message TEXT,
    priority INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    scheduled_time TIMESTAMP,
    sent_time TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT chk_notification_priority CHECK (priority >= 0),
    CONSTRAINT chk_notification_retries CHECK (retry_count >= 0 AND max_retries >= 0)
);

CREATE TABLE IF NOT EXISTS user_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT,
    is_read BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    archived_at TIMESTAMP,
    link_url VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_notification_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Level 4.15: File Management
CREATE TABLE IF NOT EXISTS file_attachments (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    mime_type VARCHAR(100),
    file_size BIGINT,
    file_path VARCHAR(500),
    storage_type VARCHAR(50) DEFAULT 'local',
    entity_type VARCHAR(50),
    entity_id INTEGER,
    upload_status VARCHAR(20) DEFAULT 'pending',
    is_public BOOLEAN DEFAULT false,
    is_temporary BOOLEAN DEFAULT false,
    expiry_date TIMESTAMP,
    checksum VARCHAR(64),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT chk_file_size CHECK (file_size >= 0),
    CONSTRAINT chk_file_upload_status CHECK (upload_status IN ('pending', 'uploading', 'completed', 'failed'))
);

-- Level 4.16: Predefined Text Templates
CREATE TABLE IF NOT EXISTS predefined_text (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    is_system_text BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_predefined_text_name UNIQUE (name)
);

-- Add indexes for better performance
CREATE INDEX idx_email_templates_type ON email_templates(template_type);
CREATE INDEX idx_email_templates_name ON email_templates(name);
CREATE INDEX idx_email_templates_active ON email_templates(is_active);

CREATE INDEX idx_notification_queue_type ON notification_queue(notification_type);
CREATE INDEX idx_notification_queue_recipient ON notification_queue(recipient_type, recipient_id);
CREATE INDEX idx_notification_queue_status ON notification_queue(status);
CREATE INDEX idx_notification_queue_schedule ON notification_queue(scheduled_time);

CREATE INDEX idx_user_notifications_user ON user_notifications(user_id);
CREATE INDEX idx_user_notifications_type ON user_notifications(notification_type);
CREATE INDEX idx_user_notifications_read ON user_notifications(is_read);
CREATE INDEX idx_user_notifications_archived ON user_notifications(is_archived);

CREATE INDEX idx_file_attachments_entity ON file_attachments(entity_type, entity_id);
CREATE INDEX idx_file_attachments_status ON file_attachments(upload_status);
CREATE INDEX idx_file_attachments_type ON file_attachments(file_type);
CREATE INDEX idx_file_attachments_expiry ON file_attachments(expiry_date);

CREATE INDEX idx_predefined_text_category ON predefined_text(category);
CREATE INDEX idx_predefined_text_name ON predefined_text(name);
CREATE INDEX idx_predefined_text_active ON predefined_text(is_active);

-- Add comments for documentation
COMMENT ON TABLE email_templates IS 'Email templates with variable support';
COMMENT ON TABLE notification_queue IS 'Queue for outgoing notifications';
COMMENT ON TABLE user_notifications IS 'User-specific notifications and alerts';
COMMENT ON TABLE file_attachments IS 'File attachment management with metadata';
COMMENT ON TABLE predefined_text IS 'Reusable text templates';

-- Add trigger for notification timestamps
CREATE OR REPLACE FUNCTION update_notification_timestamps()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_read = true AND OLD.is_read = false THEN
        NEW.read_at = CURRENT_TIMESTAMP;
    END IF;
    IF NEW.is_archived = true AND OLD.is_archived = false THEN
        NEW.archived_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_notification_timestamps
    BEFORE UPDATE ON user_notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_timestamps();

COMMIT;
