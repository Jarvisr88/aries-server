"""DMEWorks Schema Migration

This migration creates the dmeworks schema and its tables.
"""
from sqlalchemy import (
    MetaData, Table, Column, Integer, String,
    DateTime, Boolean, Text, Date, Float,
    create_engine
)

def upgrade():
    """Create dmeworks schema tables."""
    metadata = MetaData()

    # Create tbl_ability_eligibility_payer
    Table('tbl_ability_eligibility_payer', metadata,
        Column('id', Integer, primary_key=True),
        Column('code', String(50), unique=True, nullable=False),
        Column('name', String(100), nullable=False),
        Column('comments', String(100), nullable=False),
        Column('searchoptions', Text, nullable=False),
        Column('allowssubmission', Boolean, nullable=False, default=True),
        schema='dmeworks'
    )

    # Create tbl_doctor
    Table('tbl_doctor', metadata,
        Column('id', Integer, primary_key=True),
        Column('address1', String(40), nullable=False),
        Column('address2', String(40), nullable=False),
        Column('city', String(25), nullable=False),
        Column('contact', String(50), nullable=False),
        Column('courtesy', String(10), nullable=False),
        Column('fax', String(50), nullable=False),
        Column('firstname', String(25), nullable=False),
        Column('lastname', String(30), nullable=False),
        Column('licensenumber', String(16), nullable=False),
        Column('licenseexpired', Date),
        Column('medicaidnumber', String(16), nullable=False),
        Column('middlename', String(1), nullable=False),
        Column('otherid', String(16), nullable=False),
        Column('fedtaxid', String(9), nullable=False, default=''),
        Column('deanumber', String(20), nullable=False, default=''),
        Column('phone', String(50), nullable=False),
        Column('phone2', String(50), nullable=False),
        Column('state', String(2), nullable=False),
        Column('suffix', String(4), nullable=False),
        Column('title', String(50), nullable=False),
        Column('typeid', Integer),
        Column('upinnumber', String(11), nullable=False),
        Column('zip', String(10), nullable=False),
        Column('lastupdateuserid', Integer),
        Column('lastupdatedatetime', DateTime, nullable=False, default='CURRENT_TIMESTAMP'),
        Column('mir', String(255), nullable=False, default=''),
        Column('npi', String(10)),
        Column('pecosenrolled', Boolean, nullable=False, default=False),
        schema='dmeworks'
    )

    # Create tbl_doctortype
    Table('tbl_doctortype', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(50), nullable=False),
        Column('lastupdateuserid', Integer),
        Column('lastupdatedatetime', DateTime, nullable=False, default='CURRENT_TIMESTAMP'),
        schema='dmeworks'
    )

    # Create tbl_icd10
    Table('tbl_icd10', metadata,
        Column('code', String(8), primary_key=True),
        Column('description', String(255), nullable=False, default=''),
        Column('header', Boolean, nullable=False, default=False),
        Column('activedate', Date),
        Column('inactivedate', Date),
        Column('lastupdateuserid', Integer),
        Column('lastupdatedatetime', DateTime, nullable=False, default='CURRENT_TIMESTAMP'),
        schema='dmeworks'
    )

    # Create tbl_icd9
    Table('tbl_icd9', metadata,
        Column('code', String(6), primary_key=True),
        Column('description', String(255), nullable=False, default=''),
        Column('activedate', Date),
        Column('inactivedate', Date),
        Column('lastupdateuserid', Integer),
        Column('lastupdatedatetime', DateTime, nullable=False, default='CURRENT_TIMESTAMP'),
        schema='dmeworks'
    )

    # Create tbl_insurancecompany and related tables
    Table('tbl_insurancecompany', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(50), nullable=False),
        Column('address1', String(40), nullable=False, default=''),
        Column('address2', String(40), nullable=False, default=''),
        Column('city', String(25), nullable=False, default=''),
        Column('state', String(2), nullable=False, default=''),
        Column('zip', String(10), nullable=False, default=''),
        Column('contact', String(50), nullable=False, default=''),
        Column('phone', String(50), nullable=False, default=''),
        Column('fax', String(50), nullable=False, default=''),
        Column('typeid', Integer),
        Column('expectedpercent', Float),
        Column('basis', String(10), nullable=False, default='Bill'),
        Column('ecsformat', String(20), nullable=False, default='Region A'),
        schema='dmeworks'
    )

    # Create insurance company type tables
    Table('tbl_insurancecompanytype', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(50), nullable=False),
        Column('categoryid', Integer),
        schema='dmeworks'
    )

    Table('tbl_insurancecompanytype_category', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(50), nullable=False),
        schema='dmeworks'
    )

    Table('tbl_insurancecompanytype_region', metadata,
        Column('id', Integer, primary_key=True),
        Column('typeid', Integer),
        Column('regionid', Integer),
        schema='dmeworks'
    )

    Table('tbl_insurancecompanytype_subcategory', metadata,
        Column('id', Integer, primary_key=True),
        Column('categoryid', Integer),
        Column('name', String(50), nullable=False),
        schema='dmeworks'
    )

def downgrade():
    """Drop dmeworks schema tables."""
    metadata = MetaData()
    
    tables = [
        'tbl_ability_eligibility_payer',
        'tbl_doctor',
        'tbl_doctortype',
        'tbl_icd10',
        'tbl_icd9',
        'tbl_insurancecompany',
        'tbl_insurancecompanytype',
        'tbl_insurancecompanytype_category',
        'tbl_insurancecompanytype_region',
        'tbl_insurancecompanytype_subcategory'
    ]
    
    for table in tables:
        Table(table, metadata, schema='dmeworks').drop()
