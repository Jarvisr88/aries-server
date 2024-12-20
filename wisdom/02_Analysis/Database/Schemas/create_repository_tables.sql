-- Create Repository Schema Tables
-- Version: 2024-12-16_10-26
-- Description: Creates tables for the repository schema
-- Author: Cascade AI
-- Connection: postgres@localhost:5432/aries_enterprise_dev

-- Enable logging
SET client_min_messages TO NOTICE;

-- Create tables in repository schema
CREATE TABLE IF NOT EXISTS repository.tbl_batches
(
    id serial NOT NULL,
    region character varying(50),
    company character varying(50),
    workflow character varying(50),
    filename character varying(250),
    location character varying(255),
    filetype character varying(50),
    status character varying(50),
    createddate timestamp without time zone,
    statusdate timestamp without time zone,
    comment text,
    data bytea,
    archived boolean,
    CONSTRAINT tbl_batches_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS repository.tbl_certificates
(
    name character varying(50) NOT NULL,
    description character varying(100),
    data bytea,
    CONSTRAINT tbl_certificates_pkey PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS repository.tbl_companies
(
    name character varying(50) NOT NULL,
    odbcdsn character varying(50),
    server character varying(50),
    port integer,
    database character varying(50),
    CONSTRAINT tbl_companies_pkey PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS repository.tbl_globals
(
    name character varying(50) NOT NULL,
    value character varying(255),
    CONSTRAINT tbl_globals_pkey PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS repository.tbl_regions
(
    name character varying(50) NOT NULL,
    receiverid character varying(50),
    receivername character varying(50),
    receivercode character varying(50),
    submitterid character varying(50),
    submittername character varying(50),
    submitternumber character varying(50),
    submittercontact character varying(50),
    submitterphone character varying(50),
    submitteraddress1 character varying(50),
    submitteraddress2 character varying(50),
    submittercity character varying(50),
    submitterstate character varying(50),
    submitterzip character varying(50),
    production boolean,
    login character varying(50),
    password character varying(50),
    phone character varying(250),
    zipability boolean,
    updateallowable boolean,
    postzeropay boolean,
    uploadmask character varying(255),
    downloadmask character varying(255),
    CONSTRAINT tbl_regions_pkey PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS repository.tbl_variables
(
    name character varying(31) NOT NULL,
    value character varying(255) NOT NULL,
    CONSTRAINT tbl_variables_pkey PRIMARY KEY (name)
);

-- Add table comments
COMMENT ON TABLE repository.tbl_batches IS 'Stores batch processing information';
COMMENT ON TABLE repository.tbl_certificates IS 'Stores security certificates';
COMMENT ON TABLE repository.tbl_companies IS 'Stores company configuration';
COMMENT ON TABLE repository.tbl_globals IS 'Stores global system settings';
COMMENT ON TABLE repository.tbl_regions IS 'Stores region-specific configuration';
COMMENT ON TABLE repository.tbl_variables IS 'Stores system variables';
