"""
System Configuration Services
Version: 2024-12-14_19-09

Implements services for the System Configuration domain following our guiding principles:
- Role-based access control
- Secure password handling
- Audit logging
- Data validation
"""
from typing import Optional, List, Any
from datetime import datetime
import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.service import BaseService
from app.core.logging import logger
from app.models.system import User, Role, Permission, Company, AuditLog, SystemConfig, BatchProcess
from app.schemas.system import (
    UserCreate, UserUpdate,
    RoleCreate, RoleUpdate,
    PermissionCreate, PermissionUpdate,
    CompanyCreate, CompanyUpdate,
    SystemConfigCreate, SystemConfigUpdate,
    BatchProcessCreate, BatchProcessUpdate
)

class UserService(BaseService[User, UserCreate, UserUpdate]):
    """Service for managing users"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
        
    async def create(self, schema: UserCreate, **kwargs) -> User:
        """Create a new user with password hashing"""
        try:
            # Check if username or email already exists
            query = select(User).where(
                or_(
                    User.username == schema.username,
                    User.email == schema.email
                )
            )
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already registered"
                )
            
            # Hash password
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(
                schema.password.encode('utf-8'),
                salt
            )
            
            # Create user
            user_data = schema.model_dump(exclude={'password'})
            user_data['hashed_password'] = hashed_password.decode('utf-8')
            user_data.update(kwargs)
            
            db_user = User(**user_data)
            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)
            
            # Create audit log
            audit_log = AuditLog(
                user_id=kwargs.get('created_by'),
                action='create_user',
                entity_type='user',
                entity_id=db_user.id,
                details=f"Created user: {db_user.username}"
            )
            self.db.add(audit_log)
            await self.db.commit()
            
            logger.info(f"Created new user: {db_user.username}")
            return db_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create user"
            ) from e
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        try:
            query = select(User).where(
                and_(
                    User.username == username,
                    User.is_active == True
                )
            )
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            if not bcrypt.checkpw(
                password.encode('utf-8'),
                user.hashed_password.encode('utf-8')
            ):
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
    
    async def update(
        self,
        id: Any,
        schema: UserUpdate,
        current_user_id: int,
        **kwargs
    ) -> User:
        """Update a user"""
        try:
            user = await self.get(id)
            
            # Update password if provided
            if schema.password:
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(
                    schema.password.encode('utf-8'),
                    salt
                )
                schema.hashed_password = hashed_password.decode('utf-8')
            
            # Update user
            data = schema.model_dump(exclude_unset=True)
            data.update(kwargs)
            data['updated_at'] = datetime.utcnow()
            
            for field, value in data.items():
                setattr(user, field, value)
            
            # Create audit log
            audit_log = AuditLog(
                user_id=current_user_id,
                action='update_user',
                entity_type='user',
                entity_id=user.id,
                details=f"Updated user: {user.username}"
            )
            self.db.add(audit_log)
            
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Updated user: {user.username}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update user"
            ) from e
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        try:
            query = select(User).where(User.username == username)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error retrieving user by username: {str(e)}")
            return None
    
    async def get_user_roles(self, user_id: int) -> List[Role]:
        """Get all roles for a user"""
        try:
            user = await self.get(user_id)
            return user.roles
        except Exception as e:
            logger.error(f"Error retrieving user roles: {str(e)}")
            return []
    
    async def add_role(self, user_id: int, role_id: int, current_user_id: int) -> bool:
        """Add a role to a user"""
        try:
            user = await self.get(user_id)
            role = await self.db.get(Role, role_id)
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            
            if role not in user.roles:
                user.roles.append(role)
                
                # Create audit log
                audit_log = AuditLog(
                    user_id=current_user_id,
                    action='add_user_role',
                    entity_type='user',
                    entity_id=user.id,
                    details=f"Added role {role.name} to user {user.username}"
                )
                self.db.add(audit_log)
                
                await self.db.commit()
                logger.info(f"Added role {role.name} to user {user.username}")
                
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding role to user: {str(e)}")
            await self.db.rollback()
            return False
    
    async def remove_role(self, user_id: int, role_id: int, current_user_id: int) -> bool:
        """Remove a role from a user"""
        try:
            user = await self.get(user_id)
            role = await self.db.get(Role, role_id)
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            
            if role in user.roles:
                user.roles.remove(role)
                
                # Create audit log
                audit_log = AuditLog(
                    user_id=current_user_id,
                    action='remove_user_role',
                    entity_type='user',
                    entity_id=user.id,
                    details=f"Removed role {role.name} from user {user.username}"
                )
                self.db.add(audit_log)
                
                await self.db.commit()
                logger.info(f"Removed role {role.name} from user {user.username}")
                
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error removing role from user: {str(e)}")
            await self.db.rollback()
            return False

class RoleService(BaseService[Role, RoleCreate, RoleUpdate]):
    """Service for managing roles"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Role, db)
    
    async def create(self, schema: RoleCreate, current_user_id: int, **kwargs) -> Role:
        """Create a new role"""
        try:
            # Check if role name already exists
            query = select(Role).where(Role.name == schema.name)
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role name already exists"
                )
            
            # Create role
            data = schema.model_dump()
            data.update(kwargs)
            db_role = Role(**data)
            self.db.add(db_role)
            
            # Create audit log
            audit_log = AuditLog(
                user_id=current_user_id,
                action='create_role',
                entity_type='role',
                entity_id=db_role.id,
                details=f"Created role: {db_role.name}"
            )
            self.db.add(audit_log)
            
            await self.db.commit()
            await self.db.refresh(db_role)
            
            logger.info(f"Created new role: {db_role.name}")
            return db_role
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating role: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create role"
            ) from e
    
    async def get_role_permissions(self, role_id: int) -> List[Permission]:
        """Get all permissions for a role"""
        try:
            role = await self.get(role_id)
            return role.permissions
        except Exception as e:
            logger.error(f"Error retrieving role permissions: {str(e)}")
            return []
    
    async def add_permission(self, role_id: int, permission_id: int, current_user_id: int) -> bool:
        """Add a permission to a role"""
        try:
            role = await self.get(role_id)
            permission = await self.db.get(Permission, permission_id)
            
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Permission not found"
                )
            
            if permission not in role.permissions:
                role.permissions.append(permission)
                
                # Create audit log
                audit_log = AuditLog(
                    user_id=current_user_id,
                    action='add_role_permission',
                    entity_type='role',
                    entity_id=role.id,
                    details=f"Added permission {permission.name} to role {role.name}"
                )
                self.db.add(audit_log)
                
                await self.db.commit()
                logger.info(f"Added permission {permission.name} to role {role.name}")
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding permission to role: {str(e)}")
            await self.db.rollback()
            return False

class PermissionService(BaseService[Permission, PermissionCreate, PermissionUpdate]):
    """Service for managing permissions"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Permission, db)
    
    async def create(self, schema: PermissionCreate, current_user_id: int, **kwargs) -> Permission:
        """Create a new permission"""
        try:
            # Check if permission name already exists
            query = select(Permission).where(Permission.name == schema.name)
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Permission name already exists"
                )
            
            # Create permission
            data = schema.model_dump()
            data.update(kwargs)
            db_permission = Permission(**data)
            self.db.add(db_permission)
            
            # Create audit log
            audit_log = AuditLog(
                user_id=current_user_id,
                action='create_permission',
                entity_type='permission',
                entity_id=db_permission.id,
                details=f"Created permission: {db_permission.name}"
            )
            self.db.add(audit_log)
            
            await self.db.commit()
            await self.db.refresh(db_permission)
            
            logger.info(f"Created new permission: {db_permission.name}")
            return db_permission
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating permission: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create permission"
            ) from e

class CompanyService(BaseService[Company, CompanyCreate, CompanyUpdate]):
    """Service for managing companies"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Company, db)
    
    async def create(self, schema: CompanyCreate, current_user_id: int, **kwargs) -> Company:
        """Create a new company"""
        try:
            # Create company
            data = schema.model_dump()
            data.update(kwargs)
            db_company = Company(**data)
            self.db.add(db_company)
            
            # Create audit log
            audit_log = AuditLog(
                user_id=current_user_id,
                action='create_company',
                entity_type='company',
                entity_id=db_company.id,
                details=f"Created company: {db_company.name}"
            )
            self.db.add(audit_log)
            
            await self.db.commit()
            await self.db.refresh(db_company)
            
            logger.info(f"Created new company: {db_company.name}")
            return db_company
            
        except Exception as e:
            logger.error(f"Error creating company: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create company"
            ) from e
    
    async def get_active_companies(self) -> List[Company]:
        """Get all active companies"""
        try:
            query = select(Company).where(Company.is_active == True)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving active companies: {str(e)}")
            return []

class AuditLogService(BaseService[AuditLog, None, None]):
    """Service for managing audit logs"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(AuditLog, db)
    
    async def log_action(
        self,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: int,
        details: str,
        metadata: dict = None
    ) -> AuditLog:
        """Create a new audit log entry"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                metadata=metadata
            )
            self.db.add(audit_log)
            await self.db.commit()
            await self.db.refresh(audit_log)
            
            logger.info(f"Created audit log: {action} on {entity_type} {entity_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create audit log"
            ) from e
    
    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit history for a specific entity"""
        try:
            query = select(AuditLog).where(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id
                )
            ).order_by(AuditLog.created_at.desc()).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving entity history: {str(e)}")
            return []
    
    async def get_user_actions(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific user"""
        try:
            query = select(AuditLog).where(
                AuditLog.user_id == user_id
            ).order_by(AuditLog.created_at.desc()).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving user actions: {str(e)}")
            return []

class SystemConfigService(BaseService[SystemConfig, SystemConfigCreate, SystemConfigUpdate]):
    """Service for managing system configurations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(SystemConfig, db)
    
    async def create(self, schema: SystemConfigCreate, current_user_id: int, **kwargs) -> SystemConfig:
        """Create a new system configuration"""
        try:
            # Check if config key already exists for company
            query = select(SystemConfig).where(
                and_(
                    SystemConfig.company_id == schema.company_id,
                    SystemConfig.config_key == schema.config_key
                )
            )
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Configuration key already exists for this company"
                )
            
            # Create config
            data = schema.model_dump()
            data.update(kwargs)
            db_config = SystemConfig(**data)
            self.db.add(db_config)
            
            # Create audit log
            audit_log = AuditLog(
                user_id=current_user_id,
                action='create_system_config',
                entity_type='system_config',
                entity_id=db_config.id,
                details=f"Created system config: {db_config.config_key}"
            )
            self.db.add(audit_log)
            
            await self.db.commit()
            await self.db.refresh(db_config)
            
            logger.info(f"Created new system config: {db_config.config_key}")
            return db_config
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating system config: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create system config"
            ) from e
    
    async def get_company_config(self, company_id: int) -> List[SystemConfig]:
        """Get all configurations for a company"""
        try:
            query = select(SystemConfig).where(
                SystemConfig.company_id == company_id
            ).order_by(SystemConfig.config_key)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error retrieving company configs: {str(e)}")
            return []
    
    async def get_config_value(
        self,
        company_id: int,
        config_key: str,
        default: Any = None
    ) -> Any:
        """Get a specific configuration value"""
        try:
            query = select(SystemConfig).where(
                and_(
                    SystemConfig.company_id == company_id,
                    SystemConfig.config_key == config_key
                )
            )
            result = await self.db.execute(query)
            config = result.scalar_one_or_none()
            
            return config.config_value if config else default
            
        except Exception as e:
            logger.error(f"Error retrieving config value: {str(e)}")
            return default

class BatchProcessService(BaseService[BatchProcess, BatchProcessCreate, BatchProcessUpdate]):
    """Service for managing batch processes"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(BatchProcess, db)
    
    async def create(self, schema: BatchProcessCreate, current_user_id: int, **kwargs) -> BatchProcess:
        """Create a new batch process"""
        try:
            # Create process
            data = schema.model_dump()
            data.update(kwargs)
            data["status"] = "PENDING"
            
            db_process = BatchProcess(**data)
            self.db.add(db_process)
            
            # Create audit log
            audit_log = AuditLog(
                user_id=current_user_id,
                action='create_batch_process',
                entity_type='batch_process',
                entity_id=db_process.id,
                details=f"Created batch process: {db_process.process_type}"
            )
            self.db.add(audit_log)
            
            await self.db.commit()
            await self.db.refresh(db_process)
            
            logger.info(f"Created new batch process: {db_process.process_type}")
            return db_process
            
        except Exception as e:
            logger.error(f"Error creating batch process: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create batch process"
            ) from e
    
    async def update_status(
        self,
        process_id: int,
        status: str,
        result: Optional[dict] = None,
        error: Optional[str] = None
    ) -> BatchProcess:
        """Update batch process status"""
        try:
            process = await self.get(process_id)
            if not process:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Batch process not found"
                )
            
            process.status = status
            process.completed_at = datetime.utcnow() if status in ["COMPLETED", "FAILED"] else None
            
            if result is not None:
                process.result = result
            if error is not None:
                process.error = error
            
            await self.db.commit()
            await self.db.refresh(process)
            
            logger.info(f"Updated batch process status: {process.id} -> {status}")
            return process
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating batch process status: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update batch process status"
            ) from e
    
    async def get_pending_processes(self, process_type: Optional[str] = None) -> List[BatchProcess]:
        """Get pending batch processes"""
        try:
            conditions = [BatchProcess.status == "PENDING"]
            if process_type:
                conditions.append(BatchProcess.process_type == process_type)
            
            query = select(BatchProcess).where(
                and_(*conditions)
            ).order_by(BatchProcess.scheduled_start)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error retrieving pending processes: {str(e)}")
            return []
