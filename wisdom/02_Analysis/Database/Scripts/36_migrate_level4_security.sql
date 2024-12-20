-- Migration Script - Level 4.20 (Security and Access Control)
-- Generated: 2024-12-19
-- Description: Creates security, permissions, and access control tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS security_audit_logs CASCADE;
DROP TABLE IF EXISTS permission_assignments CASCADE;
DROP TABLE IF EXISTS role_permissions CASCADE;
DROP TABLE IF EXISTS permissions CASCADE;
DROP TABLE IF EXISTS role_assignments CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- Level 4.60: Role Management
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    role_type VARCHAR(50) DEFAULT 'custom',
    is_system_role BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_role_name UNIQUE (name),
    CONSTRAINT chk_role_type CHECK (
        role_type IN ('system', 'custom', 'temporary')
    )
);

CREATE TABLE IF NOT EXISTS role_assignments (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL,
    assignee_type VARCHAR(50) NOT NULL,
    assignee_id INTEGER NOT NULL,
    assigned_by INTEGER,
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_role_assignment_role FOREIGN KEY (role_id) REFERENCES roles(id),
    CONSTRAINT fk_role_assignment_assigner FOREIGN KEY (assigned_by) REFERENCES users(id),
    CONSTRAINT uq_role_assignment UNIQUE (role_id, assignee_type, assignee_id),
    CONSTRAINT chk_role_assignment_type CHECK (
        assignee_type IN ('user', 'group', 'department')
    ),
    CONSTRAINT chk_role_assignment_dates CHECK (
        valid_from <= valid_until OR valid_until IS NULL
    )
);

-- Level 4.61: Permission Management
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    resource_type VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    scope VARCHAR(50) DEFAULT 'global',
    is_system_permission BOOLEAN DEFAULT false,
    requires_approval BOOLEAN DEFAULT false,
    risk_level VARCHAR(20) DEFAULT 'low',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_permission_name UNIQUE (name),
    CONSTRAINT chk_permission_scope CHECK (
        scope IN ('global', 'organization', 'department', 'personal')
    ),
    CONSTRAINT chk_permission_risk CHECK (
        risk_level IN ('low', 'medium', 'high', 'critical')
    )
);

CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    conditions JSONB,
    granted_by INTEGER,
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_role_permission_role FOREIGN KEY (role_id) REFERENCES roles(id),
    CONSTRAINT fk_role_permission_permission FOREIGN KEY (permission_id) REFERENCES permissions(id),
    CONSTRAINT fk_role_permission_granter FOREIGN KEY (granted_by) REFERENCES users(id),
    CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id),
    CONSTRAINT chk_role_permission_dates CHECK (
        valid_from <= valid_until OR valid_until IS NULL
    )
);

CREATE TABLE IF NOT EXISTS permission_assignments (
    id SERIAL PRIMARY KEY,
    permission_id INTEGER NOT NULL,
    assignee_type VARCHAR(50) NOT NULL,
    assignee_id INTEGER NOT NULL,
    resource_id INTEGER,
    conditions JSONB,
    granted_by INTEGER,
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_permission_assignment_permission FOREIGN KEY (permission_id) REFERENCES permissions(id),
    CONSTRAINT fk_permission_assignment_granter FOREIGN KEY (granted_by) REFERENCES users(id),
    CONSTRAINT uq_permission_assignment UNIQUE (permission_id, assignee_type, assignee_id, COALESCE(resource_id, 0)),
    CONSTRAINT chk_permission_assignment_type CHECK (
        assignee_type IN ('user', 'group', 'department')
    ),
    CONSTRAINT chk_permission_assignment_dates CHECK (
        valid_from <= valid_until OR valid_until IS NULL
    )
);

-- Level 4.62: Security Audit
CREATE TABLE IF NOT EXISTS security_audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    user_id INTEGER,
    role_id INTEGER,
    permission_id INTEGER,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    action VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_id VARCHAR(50),
    old_values JSONB,
    new_values JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_security_audit_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_security_audit_role FOREIGN KEY (role_id) REFERENCES roles(id),
    CONSTRAINT fk_security_audit_permission FOREIGN KEY (permission_id) REFERENCES permissions(id),
    CONSTRAINT chk_security_audit_status CHECK (
        status IN ('success', 'failure', 'error', 'denied')
    )
);

-- Add indexes for better performance
CREATE INDEX idx_roles_type ON roles(role_type);
CREATE INDEX idx_roles_system ON roles(is_system_role);
CREATE INDEX idx_roles_active ON roles(is_active);

CREATE INDEX idx_role_assignments_role ON role_assignments(role_id);
CREATE INDEX idx_role_assignments_assignee ON role_assignments(assignee_type, assignee_id);
CREATE INDEX idx_role_assignments_dates ON role_assignments(valid_from, valid_until);
CREATE INDEX idx_role_assignments_active ON role_assignments(is_active);

CREATE INDEX idx_permissions_resource ON permissions(resource_type);
CREATE INDEX idx_permissions_action ON permissions(action_type);
CREATE INDEX idx_permissions_scope ON permissions(scope);
CREATE INDEX idx_permissions_system ON permissions(is_system_permission);
CREATE INDEX idx_permissions_risk ON permissions(risk_level);

CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission ON role_permissions(permission_id);
CREATE INDEX idx_role_permissions_dates ON role_permissions(valid_from, valid_until);
CREATE INDEX idx_role_permissions_active ON role_permissions(is_active);

CREATE INDEX idx_permission_assignments_permission ON permission_assignments(permission_id);
CREATE INDEX idx_permission_assignments_assignee ON permission_assignments(assignee_type, assignee_id);
CREATE INDEX idx_permission_assignments_resource ON permission_assignments(resource_id);
CREATE INDEX idx_permission_assignments_dates ON permission_assignments(valid_from, valid_until);
CREATE INDEX idx_permission_assignments_active ON permission_assignments(is_active);

CREATE INDEX idx_security_audit_event ON security_audit_logs(event_type, event_category);
CREATE INDEX idx_security_audit_user ON security_audit_logs(user_id);
CREATE INDEX idx_security_audit_role ON security_audit_logs(role_id);
CREATE INDEX idx_security_audit_permission ON security_audit_logs(permission_id);
CREATE INDEX idx_security_audit_resource ON security_audit_logs(resource_type, resource_id);
CREATE INDEX idx_security_audit_status ON security_audit_logs(status);
CREATE INDEX idx_security_audit_date ON security_audit_logs(created_at);

-- Add comments for documentation
COMMENT ON TABLE roles IS 'Role definitions for access control';
COMMENT ON TABLE role_assignments IS 'Role assignments to users and groups';
COMMENT ON TABLE permissions IS 'Permission definitions';
COMMENT ON TABLE role_permissions IS 'Permission assignments to roles';
COMMENT ON TABLE permission_assignments IS 'Direct permission assignments';
COMMENT ON TABLE security_audit_logs IS 'Security and access control audit logs';

-- Add trigger for security audit logging
CREATE OR REPLACE FUNCTION log_security_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO security_audit_logs (
        event_type,
        event_category,
        user_id,
        role_id,
        permission_id,
        resource_type,
        resource_id,
        action,
        status,
        old_values,
        new_values
    ) VALUES (
        CASE TG_OP
            WHEN 'INSERT' THEN 'create'
            WHEN 'UPDATE' THEN 'update'
            WHEN 'DELETE' THEN 'delete'
        END,
        TG_TABLE_NAME,
        CASE 
            WHEN TG_OP != 'DELETE' AND TG_TABLE_NAME IN ('role_assignments', 'permission_assignments') 
            AND NEW.assignee_type = 'user' THEN NEW.assignee_id
            ELSE NULL
        END,
        CASE 
            WHEN TG_TABLE_NAME = 'roles' THEN 
                CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END
            WHEN TG_TABLE_NAME IN ('role_assignments', 'role_permissions') THEN 
                CASE WHEN TG_OP = 'DELETE' THEN OLD.role_id ELSE NEW.role_id END
            ELSE NULL
        END,
        CASE 
            WHEN TG_TABLE_NAME = 'permissions' THEN 
                CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END
            WHEN TG_TABLE_NAME IN ('role_permissions', 'permission_assignments') THEN 
                CASE WHEN TG_OP = 'DELETE' THEN OLD.permission_id ELSE NEW.permission_id END
            ELSE NULL
        END,
        TG_TABLE_NAME,
        CASE 
            WHEN TG_OP = 'DELETE' THEN OLD.id
            ELSE NEW.id
        END,
        TG_OP,
        'success',
        CASE 
            WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD)
            ELSE NULL
        END,
        CASE 
            WHEN TG_OP IN ('UPDATE', 'INSERT') THEN to_jsonb(NEW)
            ELSE NULL
        END
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for security audit logging
CREATE TRIGGER log_role_changes
    AFTER INSERT OR UPDATE OR DELETE ON roles
    FOR EACH ROW
    EXECUTE FUNCTION log_security_changes();

CREATE TRIGGER log_role_assignment_changes
    AFTER INSERT OR UPDATE OR DELETE ON role_assignments
    FOR EACH ROW
    EXECUTE FUNCTION log_security_changes();

CREATE TRIGGER log_permission_changes
    AFTER INSERT OR UPDATE OR DELETE ON permissions
    FOR EACH ROW
    EXECUTE FUNCTION log_security_changes();

CREATE TRIGGER log_role_permission_changes
    AFTER INSERT OR UPDATE OR DELETE ON role_permissions
    FOR EACH ROW
    EXECUTE FUNCTION log_security_changes();

CREATE TRIGGER log_permission_assignment_changes
    AFTER INSERT OR UPDATE OR DELETE ON permission_assignments
    FOR EACH ROW
    EXECUTE FUNCTION log_security_changes();

COMMIT;
