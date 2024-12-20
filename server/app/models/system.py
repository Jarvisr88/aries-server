"""
System Configuration Domain Models
Version: 2024-12-14_17-45
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base

# Association tables for many-to-many relationships
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class TimestampMixin:
    """Mixin for created/updated timestamps"""
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    created_by: Mapped[Optional[str]] = Column(String(50))
    updated_by: Mapped[Optional[str]] = Column(String(50))

class Company(Base, TimestampMixin):
    """Company model - migrated from repository.tbl_company"""
    __tablename__ = 'companies'

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(100), nullable=False, unique=True)
    odbc_dsn: Mapped[Optional[str]] = Column(String(50))
    server: Mapped[Optional[str]] = Column(String(50))
    port: Mapped[Optional[int]] = Column(Integer)
    database: Mapped[Optional[str]] = Column(String(50))
    active: Mapped[bool] = Column(Boolean, default=True, nullable=False)

    # Relationships
    configurations: Mapped[List["SystemConfig"]] = relationship("SystemConfig", back_populates="company")
    users: Mapped[List["User"]] = relationship("User", back_populates="company")

class User(Base, TimestampMixin):
    """User model - migrated from repository.tbl_user"""
    __tablename__ = 'users'

    id: Mapped[int] = Column(Integer, primary_key=True)
    username: Mapped[str] = Column(String(50), nullable=False, unique=True)
    email: Mapped[str] = Column(String(100), nullable=False, unique=True)
    hashed_password: Mapped[str] = Column(String(255), nullable=False)
    full_name: Mapped[str] = Column(String(100), nullable=False)
    is_active: Mapped[bool] = Column(Boolean, default=True, nullable=False)
    company_id: Mapped[int] = Column(Integer, ForeignKey('companies.id'), nullable=False)

    # Relationships
    company: Mapped[Company] = relationship("Company", back_populates="users")
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users"
    )

class Role(Base, TimestampMixin):
    """Role model - migrated from repository.tbl_role"""
    __tablename__ = 'roles'

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = Column(String(255))

    # Relationships
    users: Mapped[List[User]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )

class Permission(Base, TimestampMixin):
    """Permission model - migrated from repository.tbl_permission"""
    __tablename__ = 'permissions'

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = Column(String(255))
    resource: Mapped[str] = Column(String(50), nullable=False)
    action: Mapped[str] = Column(String(50), nullable=False)

    # Relationships
    roles: Mapped[List[Role]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )

class SystemConfig(Base, TimestampMixin):
    """System Configuration model - migrated from repository.tbl_system_config"""
    __tablename__ = 'system_configs'

    id: Mapped[int] = Column(Integer, primary_key=True)
    company_id: Mapped[int] = Column(Integer, ForeignKey('companies.id'), nullable=False)
    key: Mapped[str] = Column(String(100), nullable=False)
    value: Mapped[str] = Column(String(500), nullable=False)
    description: Mapped[Optional[str]] = Column(String(255))
    is_encrypted: Mapped[bool] = Column(Boolean, default=False, nullable=False)

    # Relationships
    company: Mapped[Company] = relationship("Company", back_populates="configurations")

class AuditLog(Base, TimestampMixin):
    """Audit Log model - migrated from repository.tbl_audit_log"""
    __tablename__ = 'audit_logs'

    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey('users.id'), nullable=False)
    action: Mapped[str] = Column(String(50), nullable=False)
    resource: Mapped[str] = Column(String(50), nullable=False)
    resource_id: Mapped[Optional[int]] = Column(Integer)
    details: Mapped[Optional[str]] = Column(String(1000))
    ip_address: Mapped[Optional[str]] = Column(String(50))

    # Relationships
    user: Mapped[User] = relationship("User")
