-- This script was generated by the ERD tool in pgAdmin 4.
-- Please log an issue at https://github.com/pgadmin-org/pgadmin4/issues/new/choose if you find any bugs, including reproduction steps.
BEGIN;


CREATE TABLE IF NOT EXISTS dmeworks.tbl_ability_eligibility_payer
(
    id serial NOT NULL,
    code character varying(50) COLLATE pg_catalog."default" NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    comments character varying(100) COLLATE pg_catalog."default" NOT NULL,
    searchoptions text COLLATE pg_catalog."default" NOT NULL,
    allowssubmission boolean NOT NULL DEFAULT true,
    CONSTRAINT tbl_ability_eligibility_payer_pkey PRIMARY KEY (id),
    CONSTRAINT uq_ability_eligibility_payer UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_doctor
(
    address1 character varying(40) COLLATE pg_catalog."default" NOT NULL,
    address2 character varying(40) COLLATE pg_catalog."default" NOT NULL,
    city character varying(25) COLLATE pg_catalog."default" NOT NULL,
    contact character varying(50) COLLATE pg_catalog."default" NOT NULL,
    courtesy character varying(10) COLLATE pg_catalog."default" NOT NULL,
    fax character varying(50) COLLATE pg_catalog."default" NOT NULL,
    firstname character varying(25) COLLATE pg_catalog."default" NOT NULL,
    id serial NOT NULL,
    lastname character varying(30) COLLATE pg_catalog."default" NOT NULL,
    licensenumber character varying(16) COLLATE pg_catalog."default" NOT NULL,
    licenseexpired date,
    medicaidnumber character varying(16) COLLATE pg_catalog."default" NOT NULL,
    middlename character varying(1) COLLATE pg_catalog."default" NOT NULL,
    otherid character varying(16) COLLATE pg_catalog."default" NOT NULL,
    fedtaxid character varying(9) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    deanumber character varying(20) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    phone character varying(50) COLLATE pg_catalog."default" NOT NULL,
    phone2 character varying(50) COLLATE pg_catalog."default" NOT NULL,
    state character varying(2) COLLATE pg_catalog."default" NOT NULL,
    suffix character varying(4) COLLATE pg_catalog."default" NOT NULL,
    title character varying(50) COLLATE pg_catalog."default" NOT NULL,
    typeid integer,
    upinnumber character varying(11) COLLATE pg_catalog."default" NOT NULL,
    zip character varying(10) COLLATE pg_catalog."default" NOT NULL,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mir character varying(255) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    npi character varying(10) COLLATE pg_catalog."default" DEFAULT NULL::character varying,
    pecosenrolled boolean NOT NULL DEFAULT false,
    CONSTRAINT tbl_doctor_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_doctortype
(
    id serial NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tbl_doctortype_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_icd10
(
    code character varying(8) COLLATE pg_catalog."default" NOT NULL,
    description character varying(255) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    header boolean NOT NULL DEFAULT false,
    activedate date,
    inactivedate date,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tbl_icd10_pkey PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_icd9
(
    code character varying(6) COLLATE pg_catalog."default" NOT NULL,
    description character varying(255) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    activedate date,
    inactivedate date,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tbl_icd9_pkey PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_insurancecompany
(
    address1 character varying(40) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    address2 character varying(40) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    basis character varying(10) COLLATE pg_catalog."default" NOT NULL DEFAULT 'Bill'::character varying,
    city character varying(25) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    contact character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    ecsformat character varying(20) COLLATE pg_catalog."default" NOT NULL DEFAULT 'Region A'::character varying,
    expectedpercent double precision,
    fax character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    id serial NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    phone character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    phone2 character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    pricecodeid integer,
    printhaooninvoice boolean,
    printinvoninvoice boolean,
    state character(2) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::bpchar,
    title character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    type integer,
    zip character varying(10) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    medicarenumber character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    officeallynumber character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    zirmednumber character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    invoiceformid integer,
    medicaidnumber character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    mir character varying(255) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    groupid integer,
    availitynumber character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    abilitynumber character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    abilityeligibilitypayerid integer,
    CONSTRAINT tbl_insurancecompany_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_insurancecompanygroup
(
    id serial NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tbl_insurancecompanygroup_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_insurancecompanytype
(
    id serial NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    CONSTRAINT tbl_insurancecompanytype_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_variables
(
    name character varying(31) COLLATE pg_catalog."default" NOT NULL,
    value character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT tbl_variables_pkey PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS dmeworks.tbl_zipcode
(
    zip character varying(10) COLLATE pg_catalog."default" NOT NULL,
    state character varying(2) COLLATE pg_catalog."default" NOT NULL,
    city character varying(30) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT tbl_zipcode_pkey PRIMARY KEY (zip)
);
END;