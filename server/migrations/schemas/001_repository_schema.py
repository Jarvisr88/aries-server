"""Repository Schema Migration

This migration creates the repository schema and its tables.
"""
from sqlalchemy import (
    MetaData, Table, Column, Integer, String,
    DateTime, Boolean, LargeBinary, Text, ForeignKey,
    create_engine
)

def upgrade():
    """Create repository schema tables."""
    metadata = MetaData()

    # Create tbl_batches
    Table('tbl_batches', metadata,
        Column('id', Integer, primary_key=True),
        Column('region', String(50)),
        Column('company', String(50)),
        Column('workflow', String(50)),
        Column('filename', String(250)),
        Column('location', String(255)),
        Column('filetype', String(50)),
        Column('status', String(50)),
        Column('createddate', DateTime),
        Column('statusdate', DateTime),
        Column('comment', Text),
        Column('data', LargeBinary),
        Column('archived', Boolean),
        schema='repository'
    )

    # Create tbl_certificates
    Table('tbl_certificates', metadata,
        Column('name', String(50), primary_key=True),
        Column('description', String(100)),
        Column('data', LargeBinary),
        schema='repository'
    )

    # Create tbl_companies
    Table('tbl_companies', metadata,
        Column('name', String(50), primary_key=True),
        Column('odbcdsn', String(50)),
        Column('server', String(50)),
        Column('port', Integer),
        Column('database', String(50)),
        schema='repository'
    )

    # Create tbl_globals
    Table('tbl_globals', metadata,
        Column('name', String(50), primary_key=True),
        Column('value', String(255)),
        schema='repository'
    )

    # Create tbl_regions
    Table('tbl_regions', metadata,
        Column('name', String(50), primary_key=True),
        Column('receiverid', String(50)),
        Column('receivername', String(50)),
        Column('receivercode', String(50)),
        Column('submitterid', String(50)),
        Column('submittername', String(50)),
        Column('submitternumber', String(50)),
        Column('submittercontact', String(50)),
        Column('submitterphone', String(50)),
        Column('submitteraddress1', String(50)),
        Column('submitteraddress2', String(50)),
        Column('submittercity', String(50)),
        Column('submitterstate', String(50)),
        Column('submitterzip', String(50)),
        Column('production', Boolean),
        Column('login', String(50)),
        Column('password', String(50)),
        Column('phone', String(250)),
        Column('zipability', Boolean),
        Column('updateallowable', Boolean),
        Column('postzeropay', Boolean),
        Column('uploadmask', String(255)),
        Column('downloadmask', String(255)),
        schema='repository'
    )

    # Create tbl_variables
    Table('tbl_variables', metadata,
        Column('name', String(31), primary_key=True),
        Column('value', String(255), nullable=False),
        schema='repository'
    )

def downgrade():
    """Drop repository schema tables."""
    metadata = MetaData()
    
    tables = [
        'tbl_batches',
        'tbl_certificates',
        'tbl_companies',
        'tbl_globals',
        'tbl_regions',
        'tbl_variables'
    ]
    
    for table in tables:
        Table(table, metadata, schema='repository').drop()
