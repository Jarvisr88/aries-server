"""
System Configuration Domain Schemas
Version: 2024-12-14_17-45
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, constr, validator

# Base Schemas
class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True

# Company Schemas
class CompanyBase(BaseModel):
    name: constr(min_length=1, max_length=100)
    odbc_dsn: Optional[str] = None
    server: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    active: bool = True

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(CompanyBase):
    pass

class Company(CompanyBase, TimestampSchema):
    id: int

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    full_name: constr(min_length=1, max_length=100)
    is_active: bool = True
    company_id: int

class UserCreate(UserBase):
    password: constr(min_length=8)

class UserUpdate(UserBase):
    password: Optional[constr(min_length=8)] = None

class User(UserBase, TimestampSchema):
    id: int
    roles: List["Role"]

    class Config:
        from_attributes = True

# Role Schemas
class RoleBase(BaseModel):
    name: constr(min_length=1, max_length=50)
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    pass

class Role(RoleBase, TimestampSchema):
    id: int
    permissions: List["Permission"]

    class Config:
        from_attributes = True

# Permission Schemas
class PermissionBase(BaseModel):
    name: constr(min_length=1, max_length=50)
    description: Optional[str] = None
    resource: constr(min_length=1, max_length=50)
    action: constr(min_length=1, max_length=50)

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(PermissionBase):
    pass

class Permission(PermissionBase, TimestampSchema):
    id: int

    class Config:
        from_attributes = True

# System Config Schemas
class SystemConfigBase(BaseModel):
    company_id: int
    key: constr(min_length=1, max_length=100)
    value: constr(min_length=1, max_length=500)
    description: Optional[str] = None
    is_encrypted: bool = False

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(SystemConfigBase):
    pass

class SystemConfig(SystemConfigBase, TimestampSchema):
    id: int

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogBase(BaseModel):
    user_id: int
    action: constr(min_length=1, max_length=50)
    resource: constr(min_length=1, max_length=50)
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase, TimestampSchema):
    id: int

    class Config:
        from_attributes = True

# Update forward references
User.update_forward_refs()
Role.update_forward_refs()
