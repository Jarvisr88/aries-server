"""
Repository Schema Pydantic Models
Version: 2024-12-14_20-03

This module defines Pydantic models for repository schema operations.
"""
from typing import Optional
from pydantic import BaseModel, Field, validator

class RegionBase(BaseModel):
    """Base schema for Region"""
    receiver_id: Optional[str] = Field(None, max_length=50)
    receiver_name: Optional[str] = Field(None, max_length=50)
    receiver_code: Optional[str] = Field(None, max_length=50)
    submitter_id: Optional[str] = Field(None, max_length=50)
    submitter_name: Optional[str] = Field(None, max_length=50)
    submitter_number: Optional[str] = Field(None, max_length=50)
    submitter_contact: Optional[str] = Field(None, max_length=50)
    submitter_phone: Optional[str] = Field(None, max_length=50)
    submitter_address1: Optional[str] = Field(None, max_length=50)
    submitter_address2: Optional[str] = Field(None, max_length=50)
    submitter_city: Optional[str] = Field(None, max_length=50)
    submitter_state: Optional[str] = Field(None, max_length=50)
    submitter_zip: Optional[str] = Field(None, max_length=50)
    production: bool = False
    login: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=250)
    zip_ability: bool = False
    update_allowable: bool = False
    post_zero_pay: bool = False
    upload_mask: Optional[str] = Field(None, max_length=255)
    download_mask: Optional[str] = Field(None, max_length=255)

class RegionCreate(RegionBase):
    """Schema for creating a Region"""
    name: str = Field(..., max_length=50)

class RegionUpdate(RegionBase):
    """Schema for updating a Region"""
    pass

class Region(RegionBase):
    """Schema for Region response"""
    name: str

    class Config:
        from_attributes = True

class VariableBase(BaseModel):
    """Base schema for Variable"""
    value: str = Field(..., max_length=255)

class VariableCreate(VariableBase):
    """Schema for creating a Variable"""
    name: str = Field(..., max_length=31)

class VariableUpdate(VariableBase):
    """Schema for updating a Variable"""
    pass

class Variable(VariableBase):
    """Schema for Variable response"""
    name: str

    class Config:
        from_attributes = True
