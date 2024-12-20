"""
Dependency Injection Tests
Version: 2024-12-14_19-12
"""
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_settings,
    get_user_service,
    get_current_user,
    get_current_active_user,
    check_permission,
    get_audit_context
)
from app.core.service_provider import ServiceProvider, get_service_provider
from app.services.system import UserService

@pytest.mark.asyncio
class TestDependencies:
    async def test_get_settings(self):
        """Test settings dependency"""
        settings = get_settings()
        assert settings.PROJECT_NAME == "Aries Enterprise"
        assert settings.VERSION == "1.0.0"
        assert settings.API_V1_STR == "/api/v1"

    async def test_get_user_service(self, db: AsyncSession):
        """Test user service dependency"""
        service = get_user_service(db)
        assert isinstance(service, UserService)

    async def test_get_current_user_invalid_token(self, db: AsyncSession):
        """Test current user dependency with invalid token"""
        with pytest.raises(HTTPException) as exc:
            await get_current_user("invalid_token", get_user_service(db))
        assert exc.value.status_code == 401
        assert "Could not validate credentials" in exc.value.detail

    async def test_get_current_active_user_inactive(self, db: AsyncSession):
        """Test current active user dependency with inactive user"""
        mock_user = {"id": 1, "is_active": False}
        with pytest.raises(HTTPException) as exc:
            await get_current_active_user(mock_user)
        assert exc.value.status_code == 400
        assert "Inactive user" in exc.value.detail

    async def test_check_permission_unauthorized(self, db: AsyncSession):
        """Test permission checker with unauthorized user"""
        mock_user = {"id": 1, "is_active": True}
        permission_checker = check_permission("test_permission")
        
        with pytest.raises(HTTPException) as exc:
            await permission_checker(mock_user, get_user_service(db))
        assert exc.value.status_code == 403
        assert "Not enough permissions" in exc.value.detail

@pytest.mark.asyncio
class TestServiceProvider:
    async def test_service_provider_singleton(self, db: AsyncSession):
        """Test service provider singleton behavior"""
        provider = get_service_provider(db)
        
        # Services should be the same instance
        service1 = provider.user_service
        service2 = provider.user_service
        assert service1 is service2
        
        # Different providers should have different instances
        another_provider = get_service_provider(db)
        another_service = another_provider.user_service
        assert service1 is not another_service

    async def test_service_provider_services(self, db: AsyncSession):
        """Test all services in provider"""
        provider = get_service_provider(db)
        
        assert provider.user_service is not None
        assert provider.role_service is not None
        assert provider.permission_service is not None
        assert provider.company_service is not None
        assert provider.audit_log_service is not None
