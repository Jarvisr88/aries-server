-- Create DMEWorks Schema Tables
-- Version: 2024-12-16_10-26
-- Description: Creates tables for the dmeworks schema
-- Author: Cascade AI
-- Connection: postgres@localhost:5432/aries_enterprise_dev

-- Enable logging
SET client_min_messages TO NOTICE;

-- Create tables in dmeworks schema
CREATE TABLE IF NOT EXISTS dmeworks.tbl_ability_eligibility_payer
(
    id serial NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    comments character varying(100) NOT NULL,
    searchoptions text NOT NULL,
    allowssubmission boolean NOT NULL DEFAULT true,
    CONSTRAINT tbl_ability_eligibility_payer_pkey PRIMARY KEY (id),
    CONSTRAINT uq_ability_eligibility_payer UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_doctor
(
    id serial NOT NULL,
    address1 character varying(40) NOT NULL,
    address2 character varying(40) NOT NULL,
    city character varying(25) NOT NULL,
    contact character varying(50) NOT NULL,
    courtesy character varying(10) NOT NULL,
    fax character varying(50) NOT NULL,
    firstname character varying(25) NOT NULL,
    lastname character varying(30) NOT NULL,
    licensenumber character varying(16) NOT NULL,
    licenseexpired date,
    medicaidnumber character varying(16) NOT NULL,
    middlename character varying(1) NOT NULL,
    otherid character varying(16) NOT NULL,
    fedtaxid character varying(9) NOT NULL DEFAULT '',
    deanumber character varying(20) NOT NULL DEFAULT '',
    phone character varying(50) NOT NULL,
    phone2 character varying(50) NOT NULL,
    state character varying(2) NOT NULL,
    suffix character varying(4) NOT NULL,
    title character varying(50) NOT NULL,
    typeid integer,
    upinnumber character varying(11) NOT NULL,
    zip character varying(10) NOT NULL,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mir character varying(255) NOT NULL DEFAULT '',
    npi character varying(10),
    pecosenrolled boolean NOT NULL DEFAULT false,
    CONSTRAINT tbl_doctor_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_doctortype
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tbl_doctortype_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_icd10
(
    code character varying(8) NOT NULL,
    description character varying(255) NOT NULL DEFAULT '',
    header boolean NOT NULL DEFAULT false,
    activedate date,
    inactivedate date,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tbl_icd10_pkey PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_icd9
(
    code character varying(6) NOT NULL,
    description character varying(255) NOT NULL DEFAULT '',
    activedate date,
    inactivedate date,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tbl_icd9_pkey PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_insurancecompany
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    address1 character varying(40) NOT NULL DEFAULT '',
    address2 character varying(40) NOT NULL DEFAULT '',
    city character varying(25) NOT NULL DEFAULT '',
    state character varying(2) NOT NULL DEFAULT '',
    zip character varying(10) NOT NULL DEFAULT '',
    contact character varying(50) NOT NULL DEFAULT '',
    phone character varying(50) NOT NULL DEFAULT '',
    fax character varying(50) NOT NULL DEFAULT '',
    typeid integer,
    expectedpercent double precision,
    basis character varying(10) NOT NULL DEFAULT 'Bill',
    ecsformat character varying(20) NOT NULL DEFAULT 'Region A',
    CONSTRAINT tbl_insurancecompany_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_insurancecompanytype
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    categoryid integer,
    CONSTRAINT tbl_insurancecompanytype_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_insurancecompanytype_category
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    CONSTRAINT tbl_insurancecompanytype_category_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_insurancecompanytype_region
(
    id serial NOT NULL,
    typeid integer,
    regionid integer,
    CONSTRAINT tbl_insurancecompanytype_region_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_insurancecompanytype_subcategory
(
    id serial NOT NULL,
    categoryid integer,
    name character varying(50) NOT NULL,
    CONSTRAINT tbl_insurancecompanytype_subcategory_pkey PRIMARY KEY (id)
);

-- Add foreign key constraints
ALTER TABLE dmeworks.tbl_doctor
    ADD CONSTRAINT fk_doctor_doctortype FOREIGN KEY (typeid)
    REFERENCES dmeworks.tbl_doctortype (id);

ALTER TABLE dmeworks.tbl_insurancecompany
    ADD CONSTRAINT fk_insurancecompany_type FOREIGN KEY (typeid)
    REFERENCES dmeworks.tbl_insurancecompanytype (id);

ALTER TABLE dmeworks.tbl_insurancecompanytype
    ADD CONSTRAINT fk_insurancecompanytype_category FOREIGN KEY (categoryid)
    REFERENCES dmeworks.tbl_insurancecompanytype_category (id);

ALTER TABLE dmeworks.tbl_insurancecompanytype_region
    ADD CONSTRAINT fk_insurancecompanytype_region_type FOREIGN KEY (typeid)
    REFERENCES dmeworks.tbl_insurancecompanytype (id);

ALTER TABLE dmeworks.tbl_insurancecompanytype_subcategory
    ADD CONSTRAINT fk_insurancecompanytype_subcategory_category FOREIGN KEY (categoryid)
    REFERENCES dmeworks.tbl_insurancecompanytype_category (id);

-- Add table comments
COMMENT ON TABLE dmeworks.tbl_ability_eligibility_payer IS 'Stores eligibility payer information';
COMMENT ON TABLE dmeworks.tbl_doctor IS 'Stores healthcare provider information';
COMMENT ON TABLE dmeworks.tbl_doctortype IS 'Stores provider type classifications';
COMMENT ON TABLE dmeworks.tbl_icd10 IS 'Stores ICD-10 diagnosis codes';
COMMENT ON TABLE dmeworks.tbl_icd9 IS 'Stores ICD-9 diagnosis codes';
COMMENT ON TABLE dmeworks.tbl_insurancecompany IS 'Stores insurance company information';
COMMENT ON TABLE dmeworks.tbl_insurancecompanytype IS 'Stores insurance company type classifications';
COMMENT ON TABLE dmeworks.tbl_insurancecompanytype_category IS 'Stores insurance company categories';
COMMENT ON TABLE dmeworks.tbl_insurancecompanytype_region IS 'Maps insurance company types to regions';
COMMENT ON TABLE dmeworks.tbl_insurancecompanytype_subcategory IS 'Stores insurance company subcategories';
