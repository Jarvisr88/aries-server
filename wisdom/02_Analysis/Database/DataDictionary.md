# Aries Enterprise Data Dictionary
Version: 2024-12-19
Author: Cascade AI

## Overview
This data dictionary documents the database structure for Aries Enterprise, which consists of three main schemas:

1. **public** - Core business functionality
2. **dmeworks** - DME-specific business logic and data
3. **repository** - System configuration and repository management

## Schema: public
The public schema contains the core business functionality tables.

### Patient/Customer Management

#### customers
**Description**: Stores customer/patient information
| Column Name | Data Type | Description | Constraints | Default |
|------------|-----------|-------------|-------------|----------|
| id | serial | Unique identifier | PK | |
| first_name | varchar(100) | Customer's first name | NOT NULL | |
| last_name | varchar(100) | Customer's last name | NOT NULL | |
| date_of_birth | date | Birth date | NOT NULL | |
| status | varchar(20) | Customer status | | 'active' |

[Additional tables...]

### Medical Documentation

#### cmn_forms
**Description**: Certificate of Medical Necessity forms
| Column Name | Data Type | Description | Constraints | Default |
|------------|-----------|-------------|-------------|----------|
| id | serial | Unique identifier | PK | |
| form_type | varchar(10) | Type of CMN form | NOT NULL | |
| customer_id | integer | Reference to customer | FK(customers.id) | |

[Additional tables...]

## Schema: dmeworks
The dmeworks schema contains DME-specific business logic and data.

### tbl_ability_eligibility_payer
**Description**: Insurance payer information for eligibility checks
| Column Name | Data Type | Description | Constraints | Default |
|------------|-----------|-------------|-------------|----------|
| id | serial | Unique identifier | PK | |
| code | varchar(50) | Payer code | NOT NULL, UNIQUE | |
| name | varchar(100) | Payer name | NOT NULL | |
| comments | varchar(100) | Additional notes | NOT NULL | |
| searchoptions | text | Search configuration | NOT NULL | |
| allowssubmission | boolean | Submission flag | NOT NULL | true |

### tbl_doctor
**Description**: Doctor information and credentials
| Column Name | Data Type | Description | Constraints | Default |
|------------|-----------|-------------|-------------|----------|
| id | serial | Unique identifier | PK | |
| firstname | varchar(25) | Doctor's first name | NOT NULL | |
| lastname | varchar(30) | Doctor's last name | NOT NULL | |
| licensenumber | varchar(16) | Medical license number | NOT NULL | |
| medicaidnumber | varchar(16) | Medicaid provider number | NOT NULL | |

[Additional tables...]

## Schema: repository
The repository schema manages system configuration and repository data.

### tbl_batches
**Description**: Batch processing and workflow management
| Column Name | Data Type | Description | Constraints | Default |
|------------|-----------|-------------|-------------|----------|
| id | serial | Unique identifier | PK | |
| region | varchar(50) | Geographic region | | |
| company | varchar(50) | Company identifier | | |
| workflow | varchar(50) | Workflow type | | |
| filename | varchar(250) | Associated file | | |
| status | varchar(50) | Batch status | | |

### tbl_certificates
**Description**: Security certificates and credentials
| Column Name | Data Type | Description | Constraints | Default |
|------------|-----------|-------------|-------------|----------|
| name | varchar(50) | Certificate name | PK | |
| description | varchar(100) | Description | | |
| data | bytea | Certificate data | | |

## Relationships and Dependencies

### Public Schema
- customers → addresses (One-to-Many)
- customers → insurance_policies (One-to-Many)
- cmn_forms → customers (Many-to-One)

### DMEworks Schema
- tbl_doctor → tbl_doctor_type (Many-to-One)
- tbl_ability_eligibility_payer → tbl_insurance (One-to-Many)

### Repository Schema
- tbl_batches → tbl_companies (Many-to-One)
- tbl_regions → tbl_companies (One-to-Many)

  ## Notes
  ### 1. Timestamps
  All timestamp fields in Aries Enterprise use the 'without time zone' type to store
  datetime information. This allows for easier date and time calculations without
  worrying about timezone conversions.

  ### 2. Audit Fields
  Most tables in Aries Enterprise include audit fields to track changes made to the
  data. These fields are named `created_at`, `updated_at`, `created_by`, and
  `updated_by`, and are used to store the timestamp and user ID of the user who
  created or last updated the record.

  ### 3. JSONB Fields
  JSONB fields are used in Aries Enterprise to store flexible, schema-less data.
  These fields can store any valid JSON data, and can be easily queried and indexed
  using PostgreSQL's JSONB support.

  ### 4. Foreign Key Indexes
  Foreign key indexes are created in Aries Enterprise to improve query performance.
  These indexes are created on the foreign key columns in each table to speed up
  joins and other queries that use these columns.

## Notes
1. All timestamp fields use timezone 'without time zone'
2. Most tables include audit fields (created_at, updated_at, created_by, updated_by)
3. JSONB fields are used for flexible data storage where appropriate
4. Foreign keys generally have corresponding indexes for performance

## Indexes and Performance
Key indexes are maintained on:
- Primary keys (automatically by PostgreSQL)
- Foreign key columns
- Frequently searched columns (e.g., names, codes)
- Date ranges used in queries

## Security Considerations
- Sensitive data columns are marked for encryption
- Audit trails are maintained through history tables
- Role-based access control is implemented at the schema level
