"""
Dependency Injection Setup
Version: 2024-12-14_19-12

This module provides dependency injection setup for the application,
including database sessions, services, and configuration management.
"""
from typing import AsyncGenerator, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.system import (
    UserService,
    RoleService,
    PermissionService,
    CompanyService,
    AuditLogService
)

# Configuration Dependencies
def get_settings():
    """Get application settings"""
    return settings

# Service Dependencies
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service instance"""
    return UserService(db)

def get_role_service(db: AsyncSession = Depends(get_db)) -> RoleService:
    """Get role service instance"""
    return RoleService(db)

def get_permission_service(db: AsyncSession = Depends(get_db)) -> PermissionService:
    """Get permission service instance"""
    return PermissionService(db)

def get_company_service(db: AsyncSession = Depends(get_db)) -> CompanyService:
    """Get company service instance"""
    return CompanyService(db)

def get_audit_log_service(db: AsyncSession = Depends(get_db)) -> AuditLogService:
    """Get audit log service instance"""
    return AuditLogService(db)

# Authentication Dependencies
async def get_current_user(
    token: str,
    user_service: UserService = Depends(get_user_service)
) -> dict:
    """Get current authenticated user"""
    try:
        user = await user_service.verify_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current active user"""
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# Authorization Dependencies
def check_permission(required_permission: str) -> Callable:
    """Check if user has required permission"""
    async def permission_checker(
        current_user: dict = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)
    ) -> bool:
        user_permissions = await user_service.get_user_permissions(current_user["id"])
        if required_permission not in [p.name for p in user_permissions]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return True
    return permission_checker

# Audit Log Dependencies
async def get_audit_context(
    current_user: dict = Depends(get_current_active_user),
    audit_service: AuditLogService = Depends(get_audit_log_service)
) -> dict:
    """Get audit context for logging"""
    return {
        "user_id": current_user["id"],
        "audit_service": audit_service
    }
