"""
System Configuration Services Tests
Version: 2024-12-14_19-25
"""
import pytest
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.system import (
    CompanyService,
    UserService,
    RoleService,
    PermissionService,
    SystemConfigService,
    AuditLogService,
    BatchProcessService
)
from app.schemas.system import (
    CompanyCreate,
    UserCreate,
    RoleCreate,
    PermissionCreate,
    SystemConfigCreate,
    AuditLogCreate,
    BatchProcessCreate
)

@pytest.mark.asyncio
class TestCompanyService:
    async def test_create_company(self, db: AsyncSession):
        # Arrange
        service = CompanyService(db)
        company_data = CompanyCreate(
            name="Test Company",
            legal_name="Test Company LLC",
            tax_id="12-3456789",
            address_line1="123 Business St",
            city="Test City",
            state="TS",
            postal_code="12345",
            country="USA",
            phone="123-456-7890",
            email="contact@testcompany.com"
        )

        # Act
        company = await service.create(company_data, current_user_id=1)

        # Assert
        assert company.id is not None
        assert company.name == "Test Company"
        assert company.is_active == True

    async def test_create_duplicate_company(self, db: AsyncSession):
        # Arrange
        service = CompanyService(db)
        company_data = CompanyCreate(
            name="Test Company",
            legal_name="Test Company LLC",
            tax_id="12-3456789"
        )

        # Act & Assert
        await service.create(company_data, current_user_id=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(company_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Company with this name already exists" in exc.value.detail

@pytest.mark.asyncio
class TestUserService:
    async def test_create_user(self, db: AsyncSession):
        # Arrange
        service = UserService(db)
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            first_name="Test",
            last_name="User",
            company_id=1
        )

        # Act
        user = await service.create(user_data, current_user_id=1)

        # Assert
        assert user.id is not None
        assert user.username == "testuser"
        assert user.password_hash != "SecurePass123!"  # Password should be hashed

    async def test_create_duplicate_user(self, db: AsyncSession):
        # Arrange
        service = UserService(db)
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )

        # Act & Assert
        await service.create(user_data, current_user_id=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(user_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Username already exists" in exc.value.detail

    async def test_assign_roles(self, db: AsyncSession):
        # Arrange
        user_service = UserService(db)
        role_service = RoleService(db)
        
        user = await user_service.create(
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="SecurePass123!"
            ),
            current_user_id=1
        )
        
        role = await role_service.create(
            RoleCreate(name="Test Role"),
            current_user_id=1
        )

        # Act
        updated_user = await user_service.assign_roles(user.id, [role.id])

        # Assert
        assert len(updated_user.roles) == 1
        assert updated_user.roles[0].id == role.id

@pytest.mark.asyncio
class TestRoleService:
    async def test_create_role(self, db: AsyncSession):
        # Arrange
        service = RoleService(db)
        role_data = RoleCreate(
            name="Admin Role",
            description="Administrative access"
        )

        # Act
        role = await service.create(role_data, current_user_id=1)

        # Assert
        assert role.id is not None
        assert role.name == "Admin Role"

    async def test_assign_permissions(self, db: AsyncSession):
        # Arrange
        role_service = RoleService(db)
        permission_service = PermissionService(db)
        
        role = await role_service.create(
            RoleCreate(name="Test Role"),
            current_user_id=1
        )
        
        permission = await permission_service.create(
            PermissionCreate(
                name="test_permission",
                description="Test Permission"
            ),
            current_user_id=1
        )

        # Act
        updated_role = await role_service.assign_permissions(role.id, [permission.id])

        # Assert
        assert len(updated_role.permissions) == 1
        assert updated_role.permissions[0].id == permission.id

@pytest.mark.asyncio
class TestPermissionService:
    async def test_create_permission(self, db: AsyncSession):
        # Arrange
        service = PermissionService(db)
        permission_data = PermissionCreate(
            name="create_user",
            description="Can create new users"
        )

        # Act
        permission = await service.create(permission_data, current_user_id=1)

        # Assert
        assert permission.id is not None
        assert permission.name == "create_user"

@pytest.mark.asyncio
class TestSystemConfigService:
    async def test_create_config(self, db: AsyncSession):
        # Arrange
        service = SystemConfigService(db)
        config_data = SystemConfigCreate(
            company_id=1,
            config_key="mail_server",
            config_value="smtp.example.com",
            config_type="string",
            description="Mail server configuration"
        )

        # Act
        config = await service.create(config_data, current_user_id=1)

        # Assert
        assert config.id is not None
        assert config.config_key == "mail_server"
        assert config.config_value == "smtp.example.com"

    async def test_get_company_config(self, db: AsyncSession):
        # Arrange
        service = SystemConfigService(db)
        company_id = 1
        
        configs = [
            SystemConfigCreate(
                company_id=company_id,
                config_key=f"config_{i}",
                config_value=f"value_{i}",
                config_type="string"
            ) for i in range(3)
        ]
        
        for config in configs:
            await service.create(config, current_user_id=1)

        # Act
        company_configs = await service.get_company_config(company_id)

        # Assert
        assert len(company_configs) == 3
        assert all(c.company_id == company_id for c in company_configs)

@pytest.mark.asyncio
class TestAuditLogService:
    async def test_create_audit_log(self, db: AsyncSession):
        # Arrange
        service = AuditLogService(db)
        log_data = AuditLogCreate(
            user_id=1,
            action="CREATE",
            entity_type="USER",
            entity_id=1,
            changes={"username": "newuser"},
            ip_address="127.0.0.1"
        )

        # Act
        log = await service.create(log_data, current_user_id=1)

        # Assert
        assert log.id is not None
        assert log.action == "CREATE"
        assert log.entity_type == "USER"

    async def test_get_entity_audit_logs(self, db: AsyncSession):
        # Arrange
        service = AuditLogService(db)
        entity_type = "USER"
        entity_id = 1
        
        logs = [
            AuditLogCreate(
                user_id=1,
                action=f"ACTION_{i}",
                entity_type=entity_type,
                entity_id=entity_id,
                changes={},
                ip_address="127.0.0.1"
            ) for i in range(3)
        ]
        
        for log in logs:
            await service.create(log, current_user_id=1)

        # Act
        entity_logs = await service.get_entity_logs(entity_type, entity_id)

        # Assert
        assert len(entity_logs) == 3
        assert all(log.entity_type == entity_type for log in entity_logs)
        assert all(log.entity_id == entity_id for log in entity_logs)

@pytest.mark.asyncio
class TestBatchProcessService:
    async def test_create_batch_process(self, db: AsyncSession):
        # Arrange
        service = BatchProcessService(db)
        process_data = BatchProcessCreate(
            process_type="REPORT_GENERATION",
            parameters={"report_type": "monthly_sales"},
            scheduled_start=datetime.utcnow()
        )

        # Act
        process = await service.create(process_data, current_user_id=1)

        # Assert
        assert process.id is not None
        assert process.status == "PENDING"
        assert process.process_type == "REPORT_GENERATION"

    async def test_update_batch_process_status(self, db: AsyncSession):
        # Arrange
        service = BatchProcessService(db)
        process = await service.create(
            BatchProcessCreate(
                process_type="REPORT_GENERATION",
                parameters={"report_type": "monthly_sales"}
            ),
            current_user_id=1
        )

        # Act
        updated_process = await service.update_status(
            process.id,
            "COMPLETED",
            result={"file_url": "reports/monthly_sales.pdf"}
        )

        # Assert
        assert updated_process.status == "COMPLETED"
        assert "file_url" in updated_process.result
