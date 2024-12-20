-- Create Schemas for Aries Enterprise
-- Version: 2024-12-16_10-24
-- Description: Initial schema creation script for Aries Enterprise
-- Author: Cascade AI
-- Connection: postgres@localhost:5432/aries_enterprise_dev
-- 
-- This script follows the async-compatible pattern and includes error handling
-- as per guiding principles section 7.

-- Enable logging
SET client_min_messages TO NOTICE;

-- Create logging function
CREATE OR REPLACE FUNCTION log_schema_operation(operation text, schema_name text, status text)
RETURNS void AS $$
BEGIN
    RAISE NOTICE 'Schema Operation: % on % - Status: % at %', 
        operation, schema_name, status, CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Create repository schema with error handling
DO $$ 
DECLARE
    schema_name text := 'repository';
BEGIN
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = schema_name) THEN
            EXECUTE format('CREATE SCHEMA %I', schema_name);
            EXECUTE format('COMMENT ON SCHEMA %I IS %L', 
                schema_name, 'Schema for system configuration and repository management');
            PERFORM log_schema_operation('CREATE', schema_name, 'SUCCESS');
        ELSE
            PERFORM log_schema_operation('CHECK', schema_name, 'ALREADY EXISTS');
        END IF;
    EXCEPTION WHEN OTHERS THEN
        PERFORM log_schema_operation('CREATE', schema_name, 'FAILED: ' || SQLERRM);
        RAISE;
    END;
END $$;

-- Create dmeworks schema with error handling
DO $$ 
DECLARE
    schema_name text := 'dmeworks';
BEGIN
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = schema_name) THEN
            EXECUTE format('CREATE SCHEMA %I', schema_name);
            EXECUTE format('COMMENT ON SCHEMA %I IS %L', 
                schema_name, 'Schema for DME-specific business logic and data');
            PERFORM log_schema_operation('CREATE', schema_name, 'SUCCESS');
        ELSE
            PERFORM log_schema_operation('CHECK', schema_name, 'ALREADY EXISTS');
        END IF;
    EXCEPTION WHEN OTHERS THEN
        PERFORM log_schema_operation('CREATE', schema_name, 'FAILED: ' || SQLERRM);
        RAISE;
    END;
END $$;

-- Grant permissions with error handling
DO $$
DECLARE
    schemas text[] := ARRAY['repository', 'dmeworks'];
    schema_name text;
BEGIN
    FOREACH schema_name IN ARRAY schemas LOOP
        BEGIN
            -- Grant schema usage to postgres user (already has access as superuser)
            -- Additional users can be granted access here if needed
            PERFORM log_schema_operation('GRANT', schema_name, 'SKIPPED - Using postgres superuser');
        EXCEPTION WHEN OTHERS THEN
            PERFORM log_schema_operation('GRANT', schema_name, 'FAILED: ' || SQLERRM);
            RAISE;
        END;
    END LOOP;
END $$;

-- Configure search path with error handling
DO $$
BEGIN
    BEGIN
        ALTER DATABASE aries_enterprise_dev SET search_path TO public, repository, dmeworks;
        PERFORM log_schema_operation('SEARCH_PATH', 'ALL', 'SUCCESS');
    EXCEPTION WHEN OTHERS THEN
        PERFORM log_schema_operation('SEARCH_PATH', 'ALL', 'FAILED: ' || SQLERRM);
        RAISE;
    END;
END $$;

-- Add database comment
COMMENT ON DATABASE aries_enterprise_dev IS 'Aries Enterprise Development Database - Version 2024-12-16_10-24';

-- Log completion
SELECT log_schema_operation('SCRIPT', 'ALL', 'COMPLETED');
