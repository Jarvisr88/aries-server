-- Migration Script - Level 4.8 (Appointments and Scheduling)
-- Generated: 2024-12-19
-- Description: Creates appointment, scheduling, and calendar management tables

BEGIN;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS availability_exceptions CASCADE;
DROP TABLE IF EXISTS availability_schedules CASCADE;
DROP TABLE IF EXISTS appointment_attendees CASCADE;
DROP TABLE IF EXISTS appointments CASCADE;
DROP TABLE IF EXISTS appointment_types CASCADE;
DROP TABLE IF EXISTS calendar_sharing CASCADE;
DROP TABLE IF EXISTS calendars CASCADE;

-- Level 4.21: Base Tables (if not exist)
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

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_number VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

-- Level 4.22: Calendar Management
CREATE TABLE IF NOT EXISTS calendars (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    calendar_type VARCHAR(50),
    owner_type VARCHAR(50),
    owner_id INTEGER,
    color VARCHAR(7),
    is_public BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_calendar_name_owner UNIQUE (name, owner_type, owner_id)
);

CREATE TABLE IF NOT EXISTS calendar_sharing (
    id SERIAL PRIMARY KEY,
    calendar_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    permission_level VARCHAR(20) DEFAULT 'read',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_calendar_sharing_calendar FOREIGN KEY (calendar_id) REFERENCES calendars(id),
    CONSTRAINT fk_calendar_sharing_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_calendar_permission CHECK (
        permission_level IN ('read', 'write', 'admin')
    )
);

-- Level 4.22: Appointment Management
CREATE TABLE IF NOT EXISTS appointment_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    duration INTEGER NOT NULL, -- in minutes
    color VARCHAR(7),
    requires_approval BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT uq_appointment_type_name UNIQUE (name),
    CONSTRAINT chk_appointment_duration CHECK (duration > 0)
);

CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    calendar_id INTEGER NOT NULL,
    appointment_type_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',
    location VARCHAR(200),
    is_all_day BOOLEAN DEFAULT false,
    is_recurring BOOLEAN DEFAULT false,
    recurrence_rule TEXT,
    reminder_before INTEGER, -- in minutes
    customer_id INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_appointment_calendar FOREIGN KEY (calendar_id) REFERENCES calendars(id),
    CONSTRAINT fk_appointment_type FOREIGN KEY (appointment_type_id) REFERENCES appointment_types(id),
    CONSTRAINT fk_appointment_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT chk_appointment_times CHECK (start_time < end_time),
    CONSTRAINT chk_appointment_reminder CHECK (reminder_before > 0 OR reminder_before IS NULL)
);

CREATE TABLE IF NOT EXISTS appointment_attendees (
    id SERIAL PRIMARY KEY,
    appointment_id INTEGER NOT NULL,
    attendee_type VARCHAR(50) NOT NULL,
    attendee_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    response_date TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_appointment_attendee_appointment FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    CONSTRAINT chk_appointment_attendee_status CHECK (
        status IN ('pending', 'accepted', 'declined', 'tentative')
    )
);

-- Level 4.23: Availability Management
CREATE TABLE IF NOT EXISTS availability_schedules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    schedule_name VARCHAR(100),
    day_of_week INTEGER NOT NULL, -- 0 = Sunday, 6 = Saturday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_availability_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_availability_day CHECK (day_of_week >= 0 AND day_of_week <= 6),
    CONSTRAINT chk_availability_times CHECK (start_time < end_time)
);

CREATE TABLE IF NOT EXISTS availability_exceptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    exception_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    is_unavailable BOOLEAN DEFAULT true,
    reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),
    CONSTRAINT fk_exception_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_exception_times CHECK (
        (start_time IS NULL AND end_time IS NULL) OR
        (start_time < end_time)
    )
);

-- Add indexes for better performance
CREATE INDEX idx_calendars_owner ON calendars(owner_type, owner_id);
CREATE INDEX idx_calendars_type ON calendars(calendar_type);

CREATE INDEX idx_calendar_sharing_calendar ON calendar_sharing(calendar_id);
CREATE INDEX idx_calendar_sharing_user ON calendar_sharing(user_id);

CREATE INDEX idx_appointment_types_name ON appointment_types(name);

CREATE INDEX idx_appointments_calendar ON appointments(calendar_id);
CREATE INDEX idx_appointments_type ON appointments(appointment_type_id);
CREATE INDEX idx_appointments_customer ON appointments(customer_id);
CREATE INDEX idx_appointments_dates ON appointments(start_time, end_time);
CREATE INDEX idx_appointments_status ON appointments(status);

CREATE INDEX idx_appointment_attendees_appointment ON appointment_attendees(appointment_id);
CREATE INDEX idx_appointment_attendees_attendee ON appointment_attendees(attendee_type, attendee_id);
CREATE INDEX idx_appointment_attendees_status ON appointment_attendees(status);

CREATE INDEX idx_availability_schedules_user ON availability_schedules(user_id);
CREATE INDEX idx_availability_schedules_day ON availability_schedules(day_of_week);

CREATE INDEX idx_availability_exceptions_user ON availability_exceptions(user_id);
CREATE INDEX idx_availability_exceptions_date ON availability_exceptions(exception_date);

-- Add comments for documentation
COMMENT ON TABLE calendars IS 'Calendar management for different entities';
COMMENT ON TABLE calendar_sharing IS 'Calendar sharing permissions';
COMMENT ON TABLE appointment_types IS 'Predefined types of appointments';
COMMENT ON TABLE appointments IS 'Main appointment scheduling table';
COMMENT ON TABLE appointment_attendees IS 'Appointment participants and their responses';
COMMENT ON TABLE availability_schedules IS 'Regular availability schedules';
COMMENT ON TABLE availability_exceptions IS 'Exceptions to regular availability';

COMMIT;
