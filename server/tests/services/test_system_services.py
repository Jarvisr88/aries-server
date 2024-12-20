"""
System Configuration Services Tests
Version: 2024-12-14_19-09
"""
import pytest
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.system import (
    RoleService,
    PermissionService,
    CompanyService,
    AuditLogService
)
from app.models.system import Role, Permission, Company, AuditLog
from app.schemas.system import (
    RoleCreate,
    RoleUpdate,
    PermissionCreate,
    PermissionUpdate,
    CompanyCreate,
    CompanyUpdate
)

@pytest.mark.asyncio
class TestRoleService:
    async def test_create_role(self, db: AsyncSession):
        # Arrange
        service = RoleService(db)
        role_data = RoleCreate(
            name="test_role",
            description="Test Role"
        )

        # Act
        role = await service.create(role_data, created_by=1)

        # Assert
        assert role.id is not None
        assert role.name == "test_role"
        assert role.description == "Test Role"

    async def test_create_duplicate_role(self, db: AsyncSession):
        # Arrange
        service = RoleService(db)
        role_data = RoleCreate(
            name="test_role",
            description="Test Role"
        )

        # Act & Assert
        await service.create(role_data, created_by=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(role_data, created_by=1)
        assert exc.value.status_code == 400
        assert "Role name already exists" in exc.value.detail

    async def test_add_permission_to_role(self, db: AsyncSession):
        # Arrange
        role_service = RoleService(db)
        perm_service = PermissionService(db)

        role_data = RoleCreate(name="test_role", description="Test Role")
        perm_data = PermissionCreate(name="test_permission", description="Test Permission")

        role = await role_service.create(role_data, created_by=1)
        permission = await perm_service.create(perm_data, created_by=1)

        # Act
        result = await role_service.add_permission(role.id, permission.id, current_user_id=1)

        # Assert
        assert result == True
        permissions = await role_service.get_role_permissions(role.id)
        assert len(permissions) == 1
        assert permissions[0].name == "test_permission"

@pytest.mark.asyncio
class TestPermissionService:
    async def test_create_permission(self, db: AsyncSession):
        # Arrange
        service = PermissionService(db)
        perm_data = PermissionCreate(
            name="test_permission",
            description="Test Permission"
        )

        # Act
        permission = await service.create(perm_data, created_by=1)

        # Assert
        assert permission.id is not None
        assert permission.name == "test_permission"
        assert permission.description == "Test Permission"

    async def test_create_duplicate_permission(self, db: AsyncSession):
        # Arrange
        service = PermissionService(db)
        perm_data = PermissionCreate(
            name="test_permission",
            description="Test Permission"
        )

        # Act & Assert
        await service.create(perm_data, created_by=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(perm_data, created_by=1)
        assert exc.value.status_code == 400
        assert "Permission name already exists" in exc.value.detail

@pytest.mark.asyncio
class TestCompanyService:
    async def test_create_company(self, db: AsyncSession):
        # Arrange
        service = CompanyService(db)
        company_data = CompanyCreate(
            name="Test Company",
            contact_email="test@company.com",
            contact_phone="123-456-7890",
            is_active=True
        )

        # Act
        company = await service.create(company_data, created_by=1)

        # Assert
        assert company.id is not None
        assert company.name == "Test Company"
        assert company.contact_email == "test@company.com"
        assert company.contact_phone == "123-456-7890"
        assert company.is_active == True

    async def test_get_active_companies(self, db: AsyncSession):
        # Arrange
        service = CompanyService(db)
        active_company = CompanyCreate(
            name="Active Company",
            contact_email="active@company.com",
            is_active=True
        )
        inactive_company = CompanyCreate(
            name="Inactive Company",
            contact_email="inactive@company.com",
            is_active=False
        )

        await service.create(active_company, created_by=1)
        await service.create(inactive_company, created_by=1)

        # Act
        active_companies = await service.get_active_companies()

        # Assert
        assert len(active_companies) == 1
        assert active_companies[0].name == "Active Company"

@pytest.mark.asyncio
class TestAuditLogService:
    async def test_log_action(self, db: AsyncSession):
        # Arrange
        service = AuditLogService(db)

        # Act
        audit_log = await service.log_action(
            user_id=1,
            action="test_action",
            entity_type="test",
            entity_id=1,
            details="Test action performed",
            metadata={"key": "value"}
        )

        # Assert
        assert audit_log.id is not None
        assert audit_log.user_id == 1
        assert audit_log.action == "test_action"
        assert audit_log.entity_type == "test"
        assert audit_log.entity_id == 1
        assert audit_log.details == "Test action performed"
        assert audit_log.metadata == {"key": "value"}

    async def test_get_entity_history(self, db: AsyncSession):
        # Arrange
        service = AuditLogService(db)
        
        # Create multiple audit logs
        for i in range(3):
            await service.log_action(
                user_id=1,
                action=f"action_{i}",
                entity_type="test",
                entity_id=1,
                details=f"Test action {i}"
            )

        # Act
        history = await service.get_entity_history("test", 1, limit=2)

        # Assert
        assert len(history) == 2
        assert history[0].action == "action_2"  # Most recent first
        assert history[1].action == "action_1"

    async def test_get_user_actions(self, db: AsyncSession):
        # Arrange
        service = AuditLogService(db)
        
        # Create audit logs for different users
        await service.log_action(
            user_id=1,
            action="user1_action",
            entity_type="test",
            entity_id=1,
            details="User 1 action"
        )
        await service.log_action(
            user_id=2,
            action="user2_action",
            entity_type="test",
            entity_id=1,
            details="User 2 action"
        )

        # Act
        user1_actions = await service.get_user_actions(1)
        user2_actions = await service.get_user_actions(2)

        # Assert
        assert len(user1_actions) == 1
        assert len(user2_actions) == 1
        assert user1_actions[0].action == "user1_action"
        assert user2_actions[0].action == "user2_action"
