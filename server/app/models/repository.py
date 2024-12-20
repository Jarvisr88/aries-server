"""
Repository Schema Models
Version: 2024-12-14_20-03

This module defines models for the repository schema tables.
"""
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class Region(Base):
    """Model for repository.tbl_regions"""
    __tablename__ = "tbl_regions"
    __table_args__ = {"schema": "repository"}

    name = Column(String(50), primary_key=True)
    receiver_id = Column("receiverid", String(50))
    receiver_name = Column("receivername", String(50))
    receiver_code = Column("receivercode", String(50))
    submitter_id = Column("submitterid", String(50))
    submitter_name = Column("submittername", String(50))
    submitter_number = Column("submitternumber", String(50))
    submitter_contact = Column("submittercontact", String(50))
    submitter_phone = Column("submitterphone", String(50))
    submitter_address1 = Column("submitteraddress1", String(50))
    submitter_address2 = Column("submitteraddress2", String(50))
    submitter_city = Column("submittercity", String(50))
    submitter_state = Column("submitterstate", String(50))
    submitter_zip = Column("submitterzip", String(50))
    production = Column(Boolean, default=False)
    login = Column(String(50))
    password = Column(String(50))
    phone = Column(String(250))
    zip_ability = Column("zipability", Boolean, default=False)
    update_allowable = Column("updateallowable", Boolean, default=False)
    post_zero_pay = Column("postzeropay", Boolean, default=False)
    upload_mask = Column("uploadmask", String(255))
    download_mask = Column("downloadmask", String(255))

class Variable(Base):
    """Model for repository.tbl_variables"""
    __tablename__ = "tbl_variables"
    __table_args__ = {"schema": "repository"}

    name = Column(String(31), primary_key=True)
    value = Column(String(255), nullable=False)
