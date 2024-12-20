-- Create Missing Tables Script
-- Version: 2024-12-16_11-10
-- Description: Creates tables that exist in source but are missing in target
-- Author: Cascade AI
-- Connection: postgres@localhost:5432/aries_enterprise_dev

-- Enable logging
SET client_min_messages TO NOTICE;

-- Create custom types first
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cmn_type_enum') THEN
        CREATE TYPE public.cmn_type_enum AS ENUM ('DME 484.03', 'DME 484.04', 'DME 0484');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'answer_enum') THEN
        CREATE TYPE public.answer_enum AS ENUM ('Y', 'N', 'D');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'courtesy_enum') THEN
        CREATE TYPE public.courtesy_enum AS ENUM ('Dr.', 'Mr.', 'Mrs.', 'Ms.');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_period_enum') THEN
        CREATE TYPE public.payment_period_enum AS ENUM ('Weekly', 'Biweekly', 'Monthly');
    END IF;
END $$;

-- Create base tables first (no foreign key dependencies)
CREATE TABLE IF NOT EXISTS public.customer
(
    id serial NOT NULL,
    firstname character varying(50) NOT NULL,
    lastname character varying(50) NOT NULL,
    dateofbirth date NOT NULL,
    ssn character varying(11),
    gender character varying(1),
    maritalstatus character varying(1),
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customer_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.insurance_company
(
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    address1 character varying(100) NOT NULL,
    address2 character varying(100),
    city character varying(50) NOT NULL,
    state character varying(2) NOT NULL,
    zipcode character varying(10) NOT NULL,
    phone character varying(20),
    fax character varying(20),
    email character varying(100),
    website character varying(100),
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT insurance_company_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.equipment_type
(
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    manufacturer character varying(100),
    model character varying(50),
    hcpcs character varying(5),
    defaultprice numeric(18,2),
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT equipment_type_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.doctor
(
    id serial NOT NULL,
    courtesy public.courtesy_enum NOT NULL DEFAULT 'Dr.',
    firstname character varying(50) NOT NULL,
    lastname character varying(50) NOT NULL,
    npi character varying(10),
    upin character varying(6),
    specialty character varying(50),
    practicename character varying(100),
    address1 character varying(100) NOT NULL,
    address2 character varying(100),
    city character varying(50) NOT NULL,
    state character varying(2) NOT NULL,
    zipcode character varying(10) NOT NULL,
    phone character varying(20),
    fax character varying(20),
    email character varying(100),
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT doctor_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.audit_log
(
    id serial NOT NULL,
    tablename character varying(50) NOT NULL,
    recordid integer NOT NULL,
    action character varying(10) NOT NULL,
    changedetails text NOT NULL,
    userid integer NOT NULL,
    changedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT audit_log_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.batch_log
(
    id serial NOT NULL,
    batchid character varying(50) NOT NULL,
    processname character varying(100) NOT NULL,
    starttime timestamp without time zone NOT NULL,
    endtime timestamp without time zone,
    recordsprocessed integer NOT NULL DEFAULT 0,
    status character varying(20) NOT NULL,
    errormessage text,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT batch_log_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.batch_status
(
    id serial NOT NULL,
    batchid character varying(50) NOT NULL,
    status character varying(20) NOT NULL,
    message text,
    createdat timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT batch_status_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.batchpayment
(
    id serial NOT NULL,
    insurancecompanyid integer NOT NULL,
    checknumber character varying(14) NOT NULL,
    checkdate date NOT NULL,
    checkamount numeric(18,2) NOT NULL,
    amountused numeric(18,2) NOT NULL,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT batchpayment_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.billingtype
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    lastupdateuserid smallint,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT billingtype_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.changes
(
    tablename character varying(64) NOT NULL,
    sessionid integer NOT NULL,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT changes_pkey PRIMARY KEY (tablename, sessionid)
);

-- Add dependent tables (with foreign key constraints)
CREATE TABLE IF NOT EXISTS public.customer_address
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    addresstype character varying(20) NOT NULL,
    address1 character varying(100) NOT NULL,
    address2 character varying(100),
    city character varying(50) NOT NULL,
    state character varying(2) NOT NULL,
    zipcode character varying(10) NOT NULL,
    isprimary boolean NOT NULL DEFAULT false,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customer_address_pkey PRIMARY KEY (id),
    CONSTRAINT fk_customer_address_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id)
);

CREATE TABLE IF NOT EXISTS public.customer_contact
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    contacttype character varying(20) NOT NULL,
    contactvalue character varying(100) NOT NULL,
    isprimary boolean NOT NULL DEFAULT false,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customer_contact_pkey PRIMARY KEY (id),
    CONSTRAINT fk_customer_contact_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id)
);

CREATE TABLE IF NOT EXISTS public.customer_insurance
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    insurancecompanyid integer NOT NULL,
    policynumber character varying(50) NOT NULL,
    groupnumber character varying(50),
    startdate date NOT NULL,
    enddate date,
    isprimary boolean NOT NULL DEFAULT false,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customer_insurance_pkey PRIMARY KEY (id),
    CONSTRAINT fk_customer_insurance_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id),
    CONSTRAINT fk_customer_insurance_insurance FOREIGN KEY (insurancecompanyid)
        REFERENCES public.insurance_company(id)
);

CREATE TABLE IF NOT EXISTS public.customer_note
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    notetype character varying(20) NOT NULL,
    notetext text NOT NULL,
    createduserid smallint NOT NULL,
    createddatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customer_note_pkey PRIMARY KEY (id),
    CONSTRAINT fk_customer_note_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id)
);

CREATE TABLE IF NOT EXISTS public.equipment
(
    id serial NOT NULL,
    equipmenttypeid integer NOT NULL,
    serialnumber character varying(50) NOT NULL,
    purchasedate date,
    purchaseprice numeric(18,2),
    warrantyexpiration date,
    status character varying(20) NOT NULL DEFAULT 'Available',
    notes text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT equipment_pkey PRIMARY KEY (id),
    CONSTRAINT fk_equipment_type FOREIGN KEY (equipmenttypeid)
        REFERENCES public.equipment_type(id)
);

CREATE TABLE IF NOT EXISTS public.equipment_maintenance
(
    id serial NOT NULL,
    equipmentid integer NOT NULL,
    maintenancetype character varying(50) NOT NULL,
    maintenancedate date NOT NULL,
    performedby character varying(100) NOT NULL,
    cost numeric(18,2),
    notes text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT equipment_maintenance_pkey PRIMARY KEY (id),
    CONSTRAINT fk_equipment_maintenance_equipment FOREIGN KEY (equipmentid)
        REFERENCES public.equipment(id)
);

CREATE TABLE IF NOT EXISTS public.cmnform
(
    id serial NOT NULL,
    cmntype public.cmn_type_enum NOT NULL DEFAULT 'DME 484.03',
    initialdate date,
    reviseddate date,
    customerid integer NOT NULL,
    doctorid integer NOT NULL,
    supplierid integer NOT NULL,
    lengthofneed integer,
    CONSTRAINT cmnform_pkey PRIMARY KEY (id),
    CONSTRAINT fk_cmnform_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id),
    CONSTRAINT fk_cmnform_doctor FOREIGN KEY (doctorid)
        REFERENCES public.doctor(id)
);

CREATE TABLE IF NOT EXISTS public.cmnform_0404b
(
    cmnformid integer NOT NULL,
    answer6a public.answer_enum NOT NULL DEFAULT 'D',
    answer6b integer NOT NULL DEFAULT 0,
    answer7a public.answer_enum NOT NULL DEFAULT 'D',
    answer7b integer NOT NULL DEFAULT 0,
    CONSTRAINT cmnform_0404b_pkey PRIMARY KEY (cmnformid),
    CONSTRAINT fk_cmnform_0404b_cmnform FOREIGN KEY (cmnformid)
        REFERENCES public.cmnform(id)
);

CREATE TABLE IF NOT EXISTS public.cmnform_0484
(
    cmnformid integer NOT NULL,
    answer1_hcpcs character varying(5) NOT NULL DEFAULT '',
    answer1_mg integer,
    answer1_times integer,
    answer1_hours integer,
    CONSTRAINT cmnform_0484_pkey PRIMARY KEY (cmnformid),
    CONSTRAINT fk_cmnform_0484_cmnform FOREIGN KEY (cmnformid)
        REFERENCES public.cmnform(id)
);

CREATE TABLE IF NOT EXISTS public.ability_eligibility_request
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    customerinsuranceid integer NOT NULL,
    requesttime timestamp without time zone NOT NULL,
    requesttext text NOT NULL,
    responsetime timestamp without time zone,
    responsetext text,
    submissiontime timestamp without time zone,
    submissiontext text,
    CONSTRAINT ability_eligibility_request_pkey PRIMARY KEY (id),
    CONSTRAINT fk_ability_eligibility_request_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id),
    CONSTRAINT fk_ability_eligibility_request_customer_insurance FOREIGN KEY (customerinsuranceid)
        REFERENCES public.customer_insurance(id)
);

-- Billing and Payment Tables
CREATE TABLE IF NOT EXISTS public.payment_method
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    methodtype character varying(20) NOT NULL,
    accountnumber character varying(50),
    expirydate date,
    nameonaccount character varying(100),
    billingaddress character varying(200),
    isprimary boolean NOT NULL DEFAULT false,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT payment_method_pkey PRIMARY KEY (id),
    CONSTRAINT fk_payment_method_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id)
);

CREATE TABLE IF NOT EXISTS public.invoice
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    invoicenumber character varying(20) NOT NULL,
    invoicedate date NOT NULL,
    duedate date NOT NULL,
    subtotal numeric(18,2) NOT NULL,
    taxamount numeric(18,2) NOT NULL,
    totalamount numeric(18,2) NOT NULL,
    paidamount numeric(18,2) NOT NULL DEFAULT 0,
    status character varying(20) NOT NULL DEFAULT 'Pending',
    notes text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT invoice_pkey PRIMARY KEY (id),
    CONSTRAINT fk_invoice_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id)
);

CREATE TABLE IF NOT EXISTS public.invoice_item
(
    id serial NOT NULL,
    invoiceid integer NOT NULL,
    itemtype character varying(20) NOT NULL,
    itemid integer NOT NULL,
    description text NOT NULL,
    quantity integer NOT NULL,
    unitprice numeric(18,2) NOT NULL,
    discount numeric(18,2) NOT NULL DEFAULT 0,
    taxrate numeric(5,2) NOT NULL DEFAULT 0,
    total numeric(18,2) NOT NULL,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT invoice_item_pkey PRIMARY KEY (id),
    CONSTRAINT fk_invoice_item_invoice FOREIGN KEY (invoiceid)
        REFERENCES public.invoice(id)
);

CREATE TABLE IF NOT EXISTS public.payment
(
    id serial NOT NULL,
    invoiceid integer NOT NULL,
    paymentmethodid integer NOT NULL,
    paymentdate timestamp without time zone NOT NULL,
    amount numeric(18,2) NOT NULL,
    referencenumber character varying(50),
    status character varying(20) NOT NULL DEFAULT 'Pending',
    notes text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT payment_pkey PRIMARY KEY (id),
    CONSTRAINT fk_payment_invoice FOREIGN KEY (invoiceid)
        REFERENCES public.invoice(id),
    CONSTRAINT fk_payment_payment_method FOREIGN KEY (paymentmethodid)
        REFERENCES public.payment_method(id)
);

-- Order Management Tables
CREATE TABLE IF NOT EXISTS public.order_status
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT order_status_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.customer_order
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    orderdate timestamp without time zone NOT NULL,
    statusid integer NOT NULL,
    shippingaddressid integer NOT NULL,
    billingaddressid integer NOT NULL,
    subtotal numeric(18,2) NOT NULL,
    taxamount numeric(18,2) NOT NULL,
    totalamount numeric(18,2) NOT NULL,
    notes text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customer_order_pkey PRIMARY KEY (id),
    CONSTRAINT fk_customer_order_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id),
    CONSTRAINT fk_customer_order_status FOREIGN KEY (statusid)
        REFERENCES public.order_status(id),
    CONSTRAINT fk_customer_order_shipping_address FOREIGN KEY (shippingaddressid)
        REFERENCES public.customer_address(id),
    CONSTRAINT fk_customer_order_billing_address FOREIGN KEY (billingaddressid)
        REFERENCES public.customer_address(id)
);

CREATE TABLE IF NOT EXISTS public.order_item
(
    id serial NOT NULL,
    orderid integer NOT NULL,
    equipmenttypeid integer NOT NULL,
    quantity integer NOT NULL,
    unitprice numeric(18,2) NOT NULL,
    discount numeric(18,2) NOT NULL DEFAULT 0,
    total numeric(18,2) NOT NULL,
    notes text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT order_item_pkey PRIMARY KEY (id),
    CONSTRAINT fk_order_item_order FOREIGN KEY (orderid)
        REFERENCES public.customer_order(id),
    CONSTRAINT fk_order_item_equipment_type FOREIGN KEY (equipmenttypeid)
        REFERENCES public.equipment_type(id)
);

CREATE TABLE IF NOT EXISTS public.order_tracking
(
    id serial NOT NULL,
    orderid integer NOT NULL,
    statusid integer NOT NULL,
    notes text,
    createduserid smallint NOT NULL,
    createddatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT order_tracking_pkey PRIMARY KEY (id),
    CONSTRAINT fk_order_tracking_order FOREIGN KEY (orderid)
        REFERENCES public.customer_order(id),
    CONSTRAINT fk_order_tracking_status FOREIGN KEY (statusid)
        REFERENCES public.order_status(id)
);

-- Inventory Management Tables
CREATE TABLE IF NOT EXISTS public.warehouse
(
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    address1 character varying(100) NOT NULL,
    address2 character varying(100),
    city character varying(50) NOT NULL,
    state character varying(2) NOT NULL,
    zipcode character varying(10) NOT NULL,
    phone character varying(20),
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT warehouse_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.inventory
(
    id serial NOT NULL,
    warehouseid integer NOT NULL,
    equipmenttypeid integer NOT NULL,
    quantity integer NOT NULL DEFAULT 0,
    reorderpoint integer NOT NULL DEFAULT 0,
    reorderquantity integer NOT NULL DEFAULT 0,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT inventory_pkey PRIMARY KEY (id),
    CONSTRAINT fk_inventory_warehouse FOREIGN KEY (warehouseid)
        REFERENCES public.warehouse(id),
    CONSTRAINT fk_inventory_equipment_type FOREIGN KEY (equipmenttypeid)
        REFERENCES public.equipment_type(id)
);

CREATE TABLE IF NOT EXISTS public.inventory_transaction
(
    id serial NOT NULL,
    inventoryid integer NOT NULL,
    transactiontype character varying(20) NOT NULL,
    quantity integer NOT NULL,
    referencetype character varying(20),
    referenceid integer,
    notes text,
    createduserid smallint NOT NULL,
    createddatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT inventory_transaction_pkey PRIMARY KEY (id),
    CONSTRAINT fk_inventory_transaction_inventory FOREIGN KEY (inventoryid)
        REFERENCES public.inventory(id)
);

-- Scheduling and Appointment Tables
CREATE TABLE IF NOT EXISTS public.appointment_type
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    duration integer NOT NULL DEFAULT 30,
    color character varying(7),
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT appointment_type_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.appointment
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    appointmenttypeid integer NOT NULL,
    doctorid integer,
    starttime timestamp without time zone NOT NULL,
    endtime timestamp without time zone NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'Scheduled',
    notes text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT appointment_pkey PRIMARY KEY (id),
    CONSTRAINT fk_appointment_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id),
    CONSTRAINT fk_appointment_type FOREIGN KEY (appointmenttypeid)
        REFERENCES public.appointment_type(id),
    CONSTRAINT fk_appointment_doctor FOREIGN KEY (doctorid)
        REFERENCES public.doctor(id)
);

CREATE TABLE IF NOT EXISTS public.appointment_reminder
(
    id serial NOT NULL,
    appointmentid integer NOT NULL,
    remindertype character varying(20) NOT NULL,
    remindertime timestamp without time zone NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'Pending',
    lastsendattempt timestamp without time zone,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT appointment_reminder_pkey PRIMARY KEY (id),
    CONSTRAINT fk_appointment_reminder_appointment FOREIGN KEY (appointmentid)
        REFERENCES public.appointment(id)
);

-- Compliance and Documentation Tables
CREATE TABLE IF NOT EXISTS public.document_type
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    retentionperiod integer,
    isrequired boolean NOT NULL DEFAULT false,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT document_type_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.customer_document
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    documenttypeid integer NOT NULL,
    filename character varying(255) NOT NULL,
    filepath character varying(500) NOT NULL,
    filesize integer NOT NULL,
    mimetype character varying(100) NOT NULL,
    uploaddate timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expirydate date,
    status character varying(20) NOT NULL DEFAULT 'Active',
    notes text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customer_document_pkey PRIMARY KEY (id),
    CONSTRAINT fk_customer_document_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id),
    CONSTRAINT fk_customer_document_type FOREIGN KEY (documenttypeid)
        REFERENCES public.document_type(id)
);

CREATE TABLE IF NOT EXISTS public.compliance_checklist
(
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    frequency character varying(20) NOT NULL,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT compliance_checklist_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.compliance_checklist_item
(
    id serial NOT NULL,
    checklistid integer NOT NULL,
    itemtext text NOT NULL,
    isrequired boolean NOT NULL DEFAULT true,
    ordinal integer NOT NULL,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT compliance_checklist_item_pkey PRIMARY KEY (id),
    CONSTRAINT fk_compliance_checklist_item_checklist FOREIGN KEY (checklistid)
        REFERENCES public.compliance_checklist(id)
);

CREATE TABLE IF NOT EXISTS public.compliance_audit
(
    id serial NOT NULL,
    checklistid integer NOT NULL,
    auditdate date NOT NULL,
    auditorid smallint NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'In Progress',
    notes text,
    completeddate date,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT compliance_audit_pkey PRIMARY KEY (id),
    CONSTRAINT fk_compliance_audit_checklist FOREIGN KEY (checklistid)
        REFERENCES public.compliance_checklist(id)
);

CREATE TABLE IF NOT EXISTS public.compliance_audit_item
(
    id serial NOT NULL,
    auditid integer NOT NULL,
    checklistitemid integer NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'Pending',
    comments text,
    completeddate date,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT compliance_audit_item_pkey PRIMARY KEY (id),
    CONSTRAINT fk_compliance_audit_item_audit FOREIGN KEY (auditid)
        REFERENCES public.compliance_audit(id),
    CONSTRAINT fk_compliance_audit_item_checklist_item FOREIGN KEY (checklistitemid)
        REFERENCES public.compliance_checklist_item(id)
);

-- Reporting and Analytics Tables
CREATE TABLE IF NOT EXISTS public.report_definition
(
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    category character varying(50) NOT NULL,
    query text NOT NULL,
    parameters text,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT report_definition_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.report_schedule
(
    id serial NOT NULL,
    reportid integer NOT NULL,
    name character varying(100) NOT NULL,
    frequency character varying(20) NOT NULL,
    parameters text,
    recipients text NOT NULL,
    isactive boolean NOT NULL DEFAULT true,
    lastruntime timestamp without time zone,
    nextruntime timestamp without time zone,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT report_schedule_pkey PRIMARY KEY (id),
    CONSTRAINT fk_report_schedule_report FOREIGN KEY (reportid)
        REFERENCES public.report_definition(id)
);

CREATE TABLE IF NOT EXISTS public.report_execution
(
    id serial NOT NULL,
    reportid integer NOT NULL,
    scheduleid integer,
    starttime timestamp without time zone NOT NULL,
    endtime timestamp without time zone,
    status character varying(20) NOT NULL DEFAULT 'Running',
    parameters text,
    outputpath character varying(500),
    error text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT report_execution_pkey PRIMARY KEY (id),
    CONSTRAINT fk_report_execution_report FOREIGN KEY (reportid)
        REFERENCES public.report_definition(id),
    CONSTRAINT fk_report_execution_schedule FOREIGN KEY (scheduleid)
        REFERENCES public.report_schedule(id)
);

-- Employee Management Tables
CREATE TABLE IF NOT EXISTS public.department
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    managerid smallint,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT department_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.employee
(
    id serial NOT NULL,
    departmentid integer NOT NULL,
    employeenumber character varying(20) NOT NULL,
    firstname character varying(50) NOT NULL,
    lastname character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    phone character varying(20),
    hiredate date NOT NULL,
    terminationdate date,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT employee_pkey PRIMARY KEY (id),
    CONSTRAINT fk_employee_department FOREIGN KEY (departmentid)
        REFERENCES public.department(id)
);

CREATE TABLE IF NOT EXISTS public.employee_role
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    permissions text,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT employee_role_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.employee_role_assignment
(
    id serial NOT NULL,
    employeeid integer NOT NULL,
    roleid integer NOT NULL,
    startdate date NOT NULL,
    enddate date,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT employee_role_assignment_pkey PRIMARY KEY (id),
    CONSTRAINT fk_employee_role_assignment_employee FOREIGN KEY (employeeid)
        REFERENCES public.employee(id),
    CONSTRAINT fk_employee_role_assignment_role FOREIGN KEY (roleid)
        REFERENCES public.employee_role(id)
);

CREATE TABLE IF NOT EXISTS public.employee_schedule
(
    id serial NOT NULL,
    employeeid integer NOT NULL,
    dayofweek smallint NOT NULL,
    starttime time NOT NULL,
    endtime time NOT NULL,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT employee_schedule_pkey PRIMARY KEY (id),
    CONSTRAINT fk_employee_schedule_employee FOREIGN KEY (employeeid)
        REFERENCES public.employee(id)
);

-- System Configuration Tables
CREATE TABLE IF NOT EXISTS public.configuration_category
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT configuration_category_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.configuration_setting
(
    id serial NOT NULL,
    categoryid integer NOT NULL,
    name character varying(100) NOT NULL,
    value text NOT NULL,
    datatype character varying(20) NOT NULL,
    description text,
    isencrypted boolean NOT NULL DEFAULT false,
    isreadonly boolean NOT NULL DEFAULT false,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT configuration_setting_pkey PRIMARY KEY (id),
    CONSTRAINT fk_configuration_setting_category FOREIGN KEY (categoryid)
        REFERENCES public.configuration_category(id)
);

CREATE TABLE IF NOT EXISTS public.configuration_audit
(
    id serial NOT NULL,
    settingid integer NOT NULL,
    oldvalue text,
    newvalue text,
    changeuserid smallint NOT NULL,
    changedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT configuration_audit_pkey PRIMARY KEY (id),
    CONSTRAINT fk_configuration_audit_setting FOREIGN KEY (settingid)
        REFERENCES public.configuration_setting(id)
);

-- Communication Tables
CREATE TABLE IF NOT EXISTS public.notification_template
(
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    subject character varying(200),
    bodytemplate text NOT NULL,
    templatetype character varying(20) NOT NULL,
    parameters text,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT notification_template_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.notification
(
    id serial NOT NULL,
    templateid integer NOT NULL,
    recipienttype character varying(20) NOT NULL,
    recipientid integer NOT NULL,
    subject character varying(200),
    body text NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'Pending',
    sentattempts integer NOT NULL DEFAULT 0,
    lasterror text,
    createddatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sentdatetime timestamp without time zone,
    CONSTRAINT notification_pkey PRIMARY KEY (id),
    CONSTRAINT fk_notification_template FOREIGN KEY (templateid)
        REFERENCES public.notification_template(id)
);

CREATE TABLE IF NOT EXISTS public.communication_log
(
    id serial NOT NULL,
    notificationid integer,
    communicationtype character varying(20) NOT NULL,
    recipienttype character varying(20) NOT NULL,
    recipientid integer NOT NULL,
    subject character varying(200),
    body text NOT NULL,
    status character varying(20) NOT NULL,
    error text,
    createddatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT communication_log_pkey PRIMARY KEY (id),
    CONSTRAINT fk_communication_log_notification FOREIGN KEY (notificationid)
        REFERENCES public.notification(id)
);

-- Equipment Maintenance Tables
CREATE TABLE IF NOT EXISTS public.maintenance_schedule
(
    id serial NOT NULL,
    equipmentid integer NOT NULL,
    scheduletype character varying(20) NOT NULL,
    frequency integer NOT NULL,
    frequencyunit character varying(10) NOT NULL,
    lastmaintenancedate date,
    nextmaintenancedate date,
    description text,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT maintenance_schedule_pkey PRIMARY KEY (id),
    CONSTRAINT fk_maintenance_schedule_equipment FOREIGN KEY (equipmentid)
        REFERENCES public.equipment(id)
);

CREATE TABLE IF NOT EXISTS public.maintenance_checklist
(
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    equipmenttypeid integer NOT NULL,
    version character varying(10) NOT NULL,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT maintenance_checklist_pkey PRIMARY KEY (id),
    CONSTRAINT fk_maintenance_checklist_equipment_type FOREIGN KEY (equipmenttypeid)
        REFERENCES public.equipment_type(id)
);

CREATE TABLE IF NOT EXISTS public.maintenance_checklist_item
(
    id serial NOT NULL,
    checklistid integer NOT NULL,
    itemorder smallint NOT NULL,
    description text NOT NULL,
    requiredaction text,
    expectedvalue text,
    isrequired boolean NOT NULL DEFAULT true,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT maintenance_checklist_item_pkey PRIMARY KEY (id),
    CONSTRAINT fk_maintenance_checklist_item_checklist FOREIGN KEY (checklistid)
        REFERENCES public.maintenance_checklist(id)
);

CREATE TABLE IF NOT EXISTS public.maintenance_log
(
    id serial NOT NULL,
    equipmentid integer NOT NULL,
    checklistid integer NOT NULL,
    maintenancedate date NOT NULL,
    technicianid integer NOT NULL,
    status character varying(20) NOT NULL,
    notes text,
    completiondate date,
    nextmaintenancedate date,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT maintenance_log_pkey PRIMARY KEY (id),
    CONSTRAINT fk_maintenance_log_equipment FOREIGN KEY (equipmentid)
        REFERENCES public.equipment(id),
    CONSTRAINT fk_maintenance_log_checklist FOREIGN KEY (checklistid)
        REFERENCES public.maintenance_checklist(id),
    CONSTRAINT fk_maintenance_log_technician FOREIGN KEY (technicianid)
        REFERENCES public.employee(id)
);

CREATE TABLE IF NOT EXISTS public.maintenance_log_item
(
    id serial NOT NULL,
    maintenancelogid integer NOT NULL,
    checklistitemid integer NOT NULL,
    actualvalue text,
    status character varying(20) NOT NULL,
    notes text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT maintenance_log_item_pkey PRIMARY KEY (id),
    CONSTRAINT fk_maintenance_log_item_maintenance_log FOREIGN KEY (maintenancelogid)
        REFERENCES public.maintenance_log(id),
    CONSTRAINT fk_maintenance_log_item_checklist_item FOREIGN KEY (checklistitemid)
        REFERENCES public.maintenance_checklist_item(id)
);

-- Service History Tables
CREATE TABLE IF NOT EXISTS public.service_request
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    equipmentid integer NOT NULL,
    requestdate timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    priority character varying(20) NOT NULL,
    description text NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'Pending',
    assignedtechnicianid integer,
    scheduleddate timestamp without time zone,
    completiondate timestamp without time zone,
    resolution text,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT service_request_pkey PRIMARY KEY (id),
    CONSTRAINT fk_service_request_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id),
    CONSTRAINT fk_service_request_equipment FOREIGN KEY (equipmentid)
        REFERENCES public.equipment(id),
    CONSTRAINT fk_service_request_technician FOREIGN KEY (assignedtechnicianid)
        REFERENCES public.employee(id)
);

CREATE TABLE IF NOT EXISTS public.service_history
(
    id serial NOT NULL,
    servicerequestid integer NOT NULL,
    actiondate timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actiontype character varying(50) NOT NULL,
    description text NOT NULL,
    technicianid integer NOT NULL,
    hours decimal(5,2),
    parts text,
    cost decimal(10,2),
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT service_history_pkey PRIMARY KEY (id),
    CONSTRAINT fk_service_history_service_request FOREIGN KEY (servicerequestid)
        REFERENCES public.service_request(id),
    CONSTRAINT fk_service_history_technician FOREIGN KEY (technicianid)
        REFERENCES public.employee(id)
);

-- Customer Feedback Tables
CREATE TABLE IF NOT EXISTS public.feedback_category
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT feedback_category_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.customer_feedback
(
    id serial NOT NULL,
    customerid integer NOT NULL,
    categoryid integer NOT NULL,
    servicerequestid integer,
    rating smallint NOT NULL,
    comments text,
    submissiondate timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status character varying(20) NOT NULL DEFAULT 'New',
    response text,
    responseuserid integer,
    responsedatetime timestamp without time zone,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customer_feedback_pkey PRIMARY KEY (id),
    CONSTRAINT fk_customer_feedback_customer FOREIGN KEY (customerid)
        REFERENCES public.customer(id),
    CONSTRAINT fk_customer_feedback_category FOREIGN KEY (categoryid)
        REFERENCES public.feedback_category(id),
    CONSTRAINT fk_customer_feedback_service_request FOREIGN KEY (servicerequestid)
        REFERENCES public.service_request(id),
    CONSTRAINT fk_customer_feedback_response_user FOREIGN KEY (responseuserid)
        REFERENCES public.employee(id)
);

-- Task Management Tables
CREATE TABLE IF NOT EXISTS public.task_category
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT task_category_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.task_priority
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    sla_hours integer,
    color_code character varying(7),
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT task_priority_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.task
(
    id serial NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    categoryid integer NOT NULL,
    priorityid integer NOT NULL,
    assigneeid integer,
    createdbyid integer NOT NULL,
    duedate timestamp without time zone,
    status character varying(20) NOT NULL DEFAULT 'New',
    progress smallint NOT NULL DEFAULT 0,
    parenttaskid integer,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT task_pkey PRIMARY KEY (id),
    CONSTRAINT fk_task_category FOREIGN KEY (categoryid)
        REFERENCES public.task_category(id),
    CONSTRAINT fk_task_priority FOREIGN KEY (priorityid)
        REFERENCES public.task_priority(id),
    CONSTRAINT fk_task_assignee FOREIGN KEY (assigneeid)
        REFERENCES public.employee(id),
    CONSTRAINT fk_task_created_by FOREIGN KEY (createdbyid)
        REFERENCES public.employee(id),
    CONSTRAINT fk_task_parent FOREIGN KEY (parenttaskid)
        REFERENCES public.task(id)
);

-- Knowledge Base Tables
CREATE TABLE IF NOT EXISTS public.kb_category
(
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    parentcategoryid integer,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT kb_category_pkey PRIMARY KEY (id),
    CONSTRAINT fk_kb_category_parent FOREIGN KEY (parentcategoryid)
        REFERENCES public.kb_category(id)
);

CREATE TABLE IF NOT EXISTS public.kb_article
(
    id serial NOT NULL,
    title character varying(200) NOT NULL,
    content text NOT NULL,
    categoryid integer NOT NULL,
    authorid integer NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'Draft',
    tags text,
    viewcount integer NOT NULL DEFAULT 0,
    publisheddate timestamp without time zone,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT kb_article_pkey PRIMARY KEY (id),
    CONSTRAINT fk_kb_article_category FOREIGN KEY (categoryid)
        REFERENCES public.kb_category(id),
    CONSTRAINT fk_kb_article_author FOREIGN KEY (authorid)
        REFERENCES public.employee(id)
);

CREATE TABLE IF NOT EXISTS public.kb_article_feedback
(
    id serial NOT NULL,
    articleid integer NOT NULL,
    userid integer,
    rating smallint NOT NULL,
    comments text,
    submissiondate timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT kb_article_feedback_pkey PRIMARY KEY (id),
    CONSTRAINT fk_kb_article_feedback_article FOREIGN KEY (articleid)
        REFERENCES public.kb_article(id),
    CONSTRAINT fk_kb_article_feedback_user FOREIGN KEY (userid)
        REFERENCES public.employee(id)
);

-- Quality Control Tables
CREATE TABLE IF NOT EXISTS public.quality_checklist
(
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    equipmenttypeid integer NOT NULL,
    version character varying(10) NOT NULL,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT quality_checklist_pkey PRIMARY KEY (id),
    CONSTRAINT fk_quality_checklist_equipment_type FOREIGN KEY (equipmenttypeid)
        REFERENCES public.equipment_type(id)
);

CREATE TABLE IF NOT EXISTS public.quality_checklist_item
(
    id serial NOT NULL,
    checklistid integer NOT NULL,
    itemorder smallint NOT NULL,
    description text NOT NULL,
    testmethod text,
    acceptancecriteria text NOT NULL,
    isrequired boolean NOT NULL DEFAULT true,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT quality_checklist_item_pkey PRIMARY KEY (id),
    CONSTRAINT fk_quality_checklist_item_checklist FOREIGN KEY (checklistid)
        REFERENCES public.quality_checklist(id)
);

CREATE TABLE IF NOT EXISTS public.quality_inspection
(
    id serial NOT NULL,
    equipmentid integer NOT NULL,
    checklistid integer NOT NULL,
    inspectiondate timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    inspectorid integer NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'In Progress',
    notes text,
    completiondate timestamp without time zone,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT quality_inspection_pkey PRIMARY KEY (id),
    CONSTRAINT fk_quality_inspection_equipment FOREIGN KEY (equipmentid)
        REFERENCES public.equipment(id),
    CONSTRAINT fk_quality_inspection_checklist FOREIGN KEY (checklistid)
        REFERENCES public.quality_checklist(id),
    CONSTRAINT fk_quality_inspection_inspector FOREIGN KEY (inspectorid)
        REFERENCES public.employee(id)
);

-- Audit Logging Tables
CREATE TABLE IF NOT EXISTS public.audit_action_type
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT audit_action_type_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.audit_log
(
    id serial NOT NULL,
    actiontypeid integer NOT NULL,
    userid integer NOT NULL,
    entitytype character varying(50) NOT NULL,
    entityid integer NOT NULL,
    oldvalue text,
    newvalue text,
    ipaddress character varying(45),
    useragent text,
    actiondate timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT audit_log_pkey PRIMARY KEY (id),
    CONSTRAINT fk_audit_log_action_type FOREIGN KEY (actiontypeid)
        REFERENCES public.audit_action_type(id),
    CONSTRAINT fk_audit_log_user FOREIGN KEY (userid)
        REFERENCES public.employee(id)
);

-- System Metrics Tables
CREATE TABLE IF NOT EXISTS public.metric_type
(
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    unit character varying(20),
    datatype character varying(20) NOT NULL,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT metric_type_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.system_metric
(
    id serial NOT NULL,
    metrictypeid integer NOT NULL,
    value text NOT NULL,
    timestamp timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes text,
    CONSTRAINT system_metric_pkey PRIMARY KEY (id),
    CONSTRAINT fk_system_metric_type FOREIGN KEY (metrictypeid)
        REFERENCES public.metric_type(id)
);

CREATE TABLE IF NOT EXISTS public.performance_log
(
    id serial NOT NULL,
    component character varying(100) NOT NULL,
    operation character varying(100) NOT NULL,
    starttime timestamp without time zone NOT NULL,
    endtime timestamp without time zone NOT NULL,
    duration integer NOT NULL,
    success boolean NOT NULL,
    errordetails text,
    metadata jsonb,
    CONSTRAINT performance_log_pkey PRIMARY KEY (id)
);

-- Integration Management Tables
CREATE TABLE IF NOT EXISTS public.integration_endpoint
(
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    url character varying(500) NOT NULL,
    authtype character varying(20) NOT NULL,
    authcredentials text,
    headers jsonb,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT integration_endpoint_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.integration_mapping
(
    id serial NOT NULL,
    endpointid integer NOT NULL,
    sourcefield character varying(100) NOT NULL,
    targetfield character varying(100) NOT NULL,
    transformationrule text,
    defaultvalue text,
    isrequired boolean NOT NULL DEFAULT true,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT integration_mapping_pkey PRIMARY KEY (id),
    CONSTRAINT fk_integration_mapping_endpoint FOREIGN KEY (endpointid)
        REFERENCES public.integration_endpoint(id)
);

CREATE TABLE IF NOT EXISTS public.integration_log
(
    id serial NOT NULL,
    endpointid integer NOT NULL,
    direction character varying(10) NOT NULL,
    requestdata text,
    responsedata text,
    statuscode integer,
    success boolean NOT NULL,
    errormessage text,
    starttime timestamp without time zone NOT NULL,
    endtime timestamp without time zone NOT NULL,
    CONSTRAINT integration_log_pkey PRIMARY KEY (id),
    CONSTRAINT fk_integration_log_endpoint FOREIGN KEY (endpointid)
        REFERENCES public.integration_endpoint(id)
);

CREATE TABLE IF NOT EXISTS public.integration_schedule
(
    id serial NOT NULL,
    endpointid integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    cronexpression character varying(100) NOT NULL,
    lastruntime timestamp without time zone,
    nextruntime timestamp without time zone,
    isactive boolean NOT NULL DEFAULT true,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT integration_schedule_pkey PRIMARY KEY (id),
    CONSTRAINT fk_integration_schedule_endpoint FOREIGN KEY (endpointid)
        REFERENCES public.integration_endpoint(id)
);

-- Backup Management Table
CREATE TABLE IF NOT EXISTS public.backup_log
(
    id serial NOT NULL,
    backuptype character varying(20) NOT NULL,
    starttime timestamp without time zone NOT NULL,
    endtime timestamp without time zone,
    status character varying(20) NOT NULL DEFAULT 'In Progress',
    filesize bigint,
    filepath character varying(500),
    checksum character varying(64),
    compressiontype character varying(20),
    retentiondays integer NOT NULL,
    success boolean,
    errormessage text,
    metadata jsonb,
    initiatedby integer,
    lastupdateuserid smallint NOT NULL,
    lastupdatedatetime timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT backup_log_pkey PRIMARY KEY (id),
    CONSTRAINT fk_backup_log_initiated_by FOREIGN KEY (initiatedby)
        REFERENCES public.employee(id)
);

-- Add comments
COMMENT ON TABLE public.audit_action_type IS 'Types of audit actions';
COMMENT ON TABLE public.audit_log IS 'System-wide audit logging';
COMMENT ON TABLE public.metric_type IS 'Types of system metrics';
COMMENT ON TABLE public.system_metric IS 'System metric measurements';
COMMENT ON TABLE public.performance_log IS 'System performance monitoring';
COMMENT ON TABLE public.integration_endpoint IS 'External system integration endpoints';
COMMENT ON TABLE public.integration_mapping IS 'Field mappings for integrations';
COMMENT ON TABLE public.integration_log IS 'Integration execution history';
COMMENT ON TABLE public.integration_schedule IS 'Scheduled integration jobs';

-- Add comments
COMMENT ON TABLE public.customer_address IS 'Customer shipping and billing addresses';
COMMENT ON TABLE public.customer_contact IS 'Customer contact information (phone, email, etc)';
COMMENT ON TABLE public.customer_insurance IS 'Customer insurance policies';
COMMENT ON TABLE public.customer_note IS 'Customer-related notes and comments';
COMMENT ON TABLE public.doctor IS 'Healthcare provider information';
COMMENT ON TABLE public.equipment IS 'Medical equipment inventory';
COMMENT ON TABLE public.equipment_maintenance IS 'Equipment maintenance records';
COMMENT ON TABLE public.equipment_type IS 'Equipment categories and default settings';
COMMENT ON TABLE public.insurance_company IS 'Insurance company information';
COMMENT ON TABLE public.payment_method IS 'Customer payment methods';
COMMENT ON TABLE public.invoice IS 'Customer invoices';
COMMENT ON TABLE public.invoice_item IS 'Individual line items in invoices';
COMMENT ON TABLE public.payment IS 'Payment transactions';
COMMENT ON TABLE public.order_status IS 'Order status types';
COMMENT ON TABLE public.customer_order IS 'Customer orders';
COMMENT ON TABLE public.order_item IS 'Individual items in customer orders';
COMMENT ON TABLE public.order_tracking IS 'Order status history';
COMMENT ON TABLE public.warehouse IS 'Warehouse locations';
COMMENT ON TABLE public.inventory IS 'Equipment inventory by warehouse';
COMMENT ON TABLE public.inventory_transaction IS 'Inventory movement transactions';
COMMENT ON TABLE public.appointment_type IS 'Types of appointments available';
COMMENT ON TABLE public.appointment IS 'Customer appointments';
COMMENT ON TABLE public.appointment_reminder IS 'Appointment reminders and their status';
COMMENT ON TABLE public.document_type IS 'Types of documents that can be stored';
COMMENT ON TABLE public.customer_document IS 'Customer-related documents and files';
COMMENT ON TABLE public.compliance_checklist IS 'Compliance checklists for audits';
COMMENT ON TABLE public.compliance_checklist_item IS 'Individual items in compliance checklists';
COMMENT ON TABLE public.compliance_audit IS 'Compliance audit records';
COMMENT ON TABLE public.compliance_audit_item IS 'Individual compliance audit findings';
COMMENT ON TABLE public.report_definition IS 'Report definitions and queries';
COMMENT ON TABLE public.report_schedule IS 'Scheduled report executions';
COMMENT ON TABLE public.report_execution IS 'Report execution history';
COMMENT ON TABLE public.department IS 'Company departments';
COMMENT ON TABLE public.employee IS 'Employee information';
COMMENT ON TABLE public.employee_role IS 'Employee roles and permissions';
COMMENT ON TABLE public.employee_role_assignment IS 'Role assignments for employees';
COMMENT ON TABLE public.employee_schedule IS 'Employee work schedules';
COMMENT ON TABLE public.configuration_category IS 'System configuration categories';
COMMENT ON TABLE public.configuration_setting IS 'System configuration settings';
COMMENT ON TABLE public.configuration_audit IS 'Audit trail for configuration changes';
COMMENT ON TABLE public.notification_template IS 'Templates for system notifications';
COMMENT ON TABLE public.notification IS 'System notifications';
COMMENT ON TABLE public.communication_log IS 'Communication history log';
COMMENT ON TABLE public.maintenance_schedule IS 'Equipment maintenance schedules';
COMMENT ON TABLE public.maintenance_checklist IS 'Maintenance checklists by equipment type';
COMMENT ON TABLE public.maintenance_checklist_item IS 'Individual items in maintenance checklists';
COMMENT ON TABLE public.maintenance_log IS 'Equipment maintenance history';
COMMENT ON TABLE public.maintenance_log_item IS 'Individual maintenance checklist item results';
COMMENT ON TABLE public.service_request IS 'Customer service requests';
COMMENT ON TABLE public.service_history IS 'Service request history and actions';
COMMENT ON TABLE public.feedback_category IS 'Categories for customer feedback';
COMMENT ON TABLE public.customer_feedback IS 'Customer feedback and ratings';
COMMENT ON TABLE public.task_category IS 'Categories for tasks';
COMMENT ON TABLE public.task_priority IS 'Priority levels for tasks';
COMMENT ON TABLE public.task IS 'Task management system';
COMMENT ON TABLE public.kb_category IS 'Knowledge base article categories';
COMMENT ON TABLE public.kb_article IS 'Knowledge base articles';
COMMENT ON TABLE public.kb_article_feedback IS 'Feedback on knowledge base articles';
COMMENT ON TABLE public.quality_checklist IS 'Quality control checklists';
COMMENT ON TABLE public.quality_checklist_item IS 'Quality control checklist items';
COMMENT ON TABLE public.quality_inspection IS 'Quality control inspection records';

-- Add comment
COMMENT ON TABLE public.backup_log IS 'System backup history and metadata';
