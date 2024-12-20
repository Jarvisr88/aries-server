"""
Service Provider
Version: 2024-12-14_19-12

This module provides a centralized service provider for managing service dependencies.
"""
from typing import Dict, Type
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.system import (
    UserService,
    RoleService,
    PermissionService,
    CompanyService,
    AuditLogService
)

class ServiceProvider:
    """Service provider for managing service dependencies"""
    
    def __init__(self, db: AsyncSession):
        self._db = db
        self._services: Dict[Type, object] = {}
    
    def _get_or_create(self, service_class: Type) -> object:
        """Get an existing service instance or create a new one"""
        if service_class not in self._services:
            self._services[service_class] = service_class(self._db)
        return self._services[service_class]
    
    @property
    def user_service(self) -> UserService:
        """Get user service instance"""
        return self._get_or_create(UserService)
    
    @property
    def role_service(self) -> RoleService:
        """Get role service instance"""
        return self._get_or_create(RoleService)
    
    @property
    def permission_service(self) -> PermissionService:
        """Get permission service instance"""
        return self._get_or_create(PermissionService)
    
    @property
    def company_service(self) -> CompanyService:
        """Get company service instance"""
        return self._get_or_create(CompanyService)
    
    @property
    def audit_log_service(self) -> AuditLogService:
        """Get audit log service instance"""
        return self._get_or_create(AuditLogService)

def get_service_provider(db: AsyncSession) -> ServiceProvider:
    """Get service provider instance"""
    return ServiceProvider(db)
