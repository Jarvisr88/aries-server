# Consolidated Technical Data Architecture Analysis

## Data Layer Overview

### Core Database Structure
```sql
-- Example schema structure
CREATE SCHEMA dme;
CREATE SCHEMA hme;
CREATE SCHEMA shared;

-- Shared tables for common functionality
CREATE TABLE shared.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Module-specific tables with references
CREATE TABLE dme.equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    inventory_count INTEGER NOT NULL,
    CONSTRAINT positive_inventory CHECK (inventory_count >= 0)
);

CREATE TABLE hme.insurance_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL,
    submitted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'denied', 'processing'))
);
```

### Data Access Patterns

#### SQLAlchemy Models
```python
from sqlalchemy import Column, ForeignKey, String, UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    
    # Relationships
    dme_orders = relationship("DMEOrder", back_populates="user")
    hme_claims = relationship("HMEClaim", back_populates="user")

class DMEOrder(Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": "dme"}

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("shared.users.id"))
    
    # Relationships
    user = relationship("User", back_populates="dme_orders")
```

### Data Validation Layer

#### Pydantic Models
```python
from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    
    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "strongpassword123"
            }
        }

class UserInDB(UserBase):
    id: UUID4
    created_at: datetime
    is_active: bool
```

## Data Flow Architecture

### 1. Request/Response Flow
```python
@router.post("/users/", response_model=schemas.User)
async def create_user(
    user_in: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Validate input
    validated_data = UserCreate(**user_in.dict())
    
    # Process data
    user = await crud.user.create(db, obj_in=validated_data)
    
    # Return validated response
    return schemas.User.from_orm(user)
```

### 2. Caching Strategy
```python
from app.core.cache import Cache
from app.core.config import settings

cache = Cache(
    url=settings.REDIS_URL,
    default_ttl=3600
)

class UserService:
    async def get_user(self, user_id: UUID) -> User:
        # Try cache first
        cached_user = await cache.get(f"user:{user_id}")
        if cached_user:
            return User.parse_raw(cached_user)
            
        # Fetch from database
        user = await self.db.get(User, user_id)
        if user:
            # Cache for future requests
            await cache.set(
                f"user:{user_id}",
                user.json(),
                ttl=3600
            )
        return user
```

## Data Migration Strategy

### 1. Alembic Configuration
```python
# alembic/env.py
from alembic import context
from app.db.base import Base
from app.core.config import settings

config = context.config
target_metadata = Base.metadata

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_async_engine(
        settings.DATABASE_URL,
        future=True,
        echo=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
```

### 2. Migration Scripts
```python
# alembic/versions/xxx_create_initial_tables.py
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Create schemas
    op.execute('CREATE SCHEMA IF NOT EXISTS dme')
    op.execute('CREATE SCHEMA IF NOT EXISTS hme')
    op.execute('CREATE SCHEMA IF NOT EXISTS shared')
    
    # Create tables
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='shared'
    )
```

## Data Security

### 1. Row Level Security
```sql
-- Enable RLS on sensitive tables
ALTER TABLE dme.patient_records ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY patient_access_policy ON dme.patient_records
    FOR ALL
    TO authenticated_users
    USING (
        current_user_id() = created_by_user_id
        OR 
        has_permission('view_all_patients')
    );
```

### 2. Data Encryption
```python
from cryptography.fernet import Fernet
from app.core.config import settings

class EncryptionService:
    def __init__(self):
        self.fernet = Fernet(settings.ENCRYPTION_KEY)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        return self.fernet.decrypt(encrypted_data.encode()).decode()
```

## Data Backup and Recovery

### 1. Backup Strategy
```python
from app.core.backup import BackupService
from app.core.config import settings

backup_service = BackupService(
    storage_url=settings.BACKUP_STORAGE_URL,
    retention_days=30
)

@periodic_task(run_every=timedelta(days=1))
async def backup_database():
    """Daily database backup"""
    try:
        await backup_service.create_backup(
            include_schemas=['dme', 'hme', 'shared'],
            compress=True
        )
    except Exception as e:
        log.error(f"Backup failed: {e}")
        notify_admin("Database backup failed")
```

## Performance Optimization

### 1. Index Strategy
```sql
-- Create indexes for frequently accessed columns
CREATE INDEX idx_equipment_category ON dme.equipment(category);
CREATE INDEX idx_claims_status ON hme.insurance_claims(status);

-- Create composite indexes for common query patterns
CREATE INDEX idx_claims_patient_status ON hme.insurance_claims(patient_id, status);
```

### 2. Query Optimization
```python
from sqlalchemy import select
from sqlalchemy.orm import joinedload

async def get_user_with_orders(user_id: UUID) -> User:
    query = (
        select(User)
        .options(
            joinedload(User.dme_orders),
            joinedload(User.hme_claims)
        )
        .where(User.id == user_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

## Monitoring and Metrics

### 1. Database Metrics
```python
from app.core.monitoring import DBMetrics

db_metrics = DBMetrics()

@app.on_event("startup")
async def setup_db_monitoring():
    await db_metrics.setup(
        collect_query_stats=True,
        slow_query_threshold_ms=1000,
        connection_pool_metrics=True
    )
```

### 2. Data Quality Monitoring
```python
from app.core.monitoring import DataQualityMonitor

dq_monitor = DataQualityMonitor()

@periodic_task(run_every=timedelta(hours=1))
async def check_data_quality():
    """Hourly data quality checks"""
    await dq_monitor.run_checks([
        check_referential_integrity(),
        check_data_freshness(),
        check_null_ratios()
    ])
```

_Note: This consolidated architecture leverages best practices from all available documentation while maintaining consistency with the modular approach and security requirements._
