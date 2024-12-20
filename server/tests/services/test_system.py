"""
System Configuration Services Tests
Version: 2024-12-14_19-07
"""
import pytest
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.system import UserService
from app.models.system import User, Role, Permission
from app.schemas.system import UserCreate, UserUpdate

@pytest.mark.asyncio
class TestUserService:
    async def test_create_user(self, db: AsyncSession):
        # Arrange
        service = UserService(db)
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            is_active=True
        )

        # Act
        user = await service.create(user_data, created_by=1)

        # Assert
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active == True
        assert user.hashed_password is not None
        assert user.hashed_password != "password123"

    async def test_create_duplicate_user(self, db: AsyncSession):
        # Arrange
        service = UserService(db)
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            is_active=True
        )

        # Act & Assert
        await service.create(user_data, created_by=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(user_data, created_by=1)
        assert exc.value.status_code == 400
        assert "Username or email already registered" in exc.value.detail

    async def test_authenticate_user(self, db: AsyncSession):
        # Arrange
        service = UserService(db)
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        await service.create(user_data, created_by=1)

        # Act
        user = await service.authenticate("testuser", "password123")

        # Assert
        assert user is not None
        assert user.username == "testuser"

    async def test_authenticate_user_wrong_password(self, db: AsyncSession):
        # Arrange
        service = UserService(db)
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        await service.create(user_data, created_by=1)

        # Act
        user = await service.authenticate("testuser", "wrongpassword")

        # Assert
        assert user is None

    async def test_update_user(self, db: AsyncSession):
        # Arrange
        service = UserService(db)
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        user = await service.create(user_data, created_by=1)

        update_data = UserUpdate(
            first_name="Updated",
            last_name="Name"
        )

        # Act
        updated_user = await service.update(user.id, update_data, current_user_id=1)

        # Assert
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.username == "testuser"  # Unchanged

    async def test_add_role_to_user(self, db: AsyncSession):
        # Arrange
        service = UserService(db)
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        user = await service.create(user_data, created_by=1)

        role = Role(name="test_role", description="Test Role")
        db.add(role)
        await db.commit()
        await db.refresh(role)

        # Act
        result = await service.add_role(user.id, role.id, current_user_id=1)

        # Assert
        assert result == True
        user_roles = await service.get_user_roles(user.id)
        assert len(user_roles) == 1
        assert user_roles[0].name == "test_role"

    async def test_remove_role_from_user(self, db: AsyncSession):
        # Arrange
        service = UserService(db)
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        user = await service.create(user_data, created_by=1)

        role = Role(name="test_role", description="Test Role")
        db.add(role)
        await db.commit()
        await db.refresh(role)

        await service.add_role(user.id, role.id, current_user_id=1)

        # Act
        result = await service.remove_role(user.id, role.id, current_user_id=1)

        # Assert
        assert result == True
        user_roles = await service.get_user_roles(user.id)
        assert len(user_roles) == 0
