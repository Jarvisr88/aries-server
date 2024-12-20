# Database Analysis

## Current Database Architecture

### Schema Overview
```sql
-- Current SQL Server Schema
CREATE SCHEMA dme;
CREATE SCHEMA hme;
CREATE SCHEMA shared;

-- Core Tables
CREATE TABLE shared.users (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    email NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2
);

CREATE TABLE dme.equipment (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    name NVARCHAR(255) NOT NULL,
    category NVARCHAR(50) NOT NULL,
    status NVARCHAR(50) NOT NULL,
    last_maintenance DATETIME2,
    next_maintenance DATETIME2,
    created_by UNIQUEIDENTIFIER REFERENCES shared.users(id),
    created_at DATETIME2 DEFAULT GETDATE()
);
```

## Migration Strategy

### 1. Schema Migration to PostgreSQL
```sql
-- PostgreSQL Schema
CREATE SCHEMA dme;
CREATE SCHEMA hme;
CREATE SCHEMA shared;

-- Core Tables with PostgreSQL Types
CREATE TABLE shared.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

CREATE TABLE dme.equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category equipment_category NOT NULL,
    status equipment_status NOT NULL,
    last_maintenance TIMESTAMPTZ,
    next_maintenance TIMESTAMPTZ,
    created_by UUID REFERENCES shared.users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Data Type Mapping
| SQL Server | PostgreSQL | SQLAlchemy | Python |
|------------|------------|------------|---------|
| UNIQUEIDENTIFIER | UUID | UUID | uuid.UUID |
| NVARCHAR | VARCHAR | String | str |
| DATETIME2 | TIMESTAMPTZ | DateTime | datetime |
| BIT | BOOLEAN | Boolean | bool |
| DECIMAL | NUMERIC | Numeric | decimal.Decimal |

### 3. SQLAlchemy Models
```python
# app/models/base.py
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

# app/models/user.py
class User(BaseModel):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'shared'}
    
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
```

## Performance Optimization

### 1. Indexing Strategy
```sql
-- Core Indexes
CREATE INDEX idx_users_email ON shared.users(email);
CREATE INDEX idx_equipment_category ON dme.equipment(category);
CREATE INDEX idx_equipment_status ON dme.equipment(status);

-- Composite Indexes for Common Queries
CREATE INDEX idx_equipment_category_status 
ON dme.equipment(category, status);
```

### 2. Query Optimization
```python
# app/crud/equipment.py
from sqlalchemy import select
from sqlalchemy.orm import joinedload

async def get_equipment_with_details(
    db: AsyncSession,
    equipment_id: UUID
) -> Optional[Equipment]:
    query = (
        select(Equipment)
        .options(
            joinedload(Equipment.maintenance_records),
            joinedload(Equipment.created_by)
        )
        .where(Equipment.id == equipment_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

## Data Migration

### 1. Migration Scripts
```python
# scripts/migrate_data.py
import asyncio
from sqlalchemy import create_engine
from app.db.session import async_session
from app.models import User, Equipment

async def migrate_users():
    """Migrate users from SQL Server to PostgreSQL"""
    source_engine = create_engine(SQLSERVER_URL)
    
    async with async_session() as session:
        with source_engine.connect() as conn:
            users = conn.execute(
                "SELECT * FROM shared.users"
            ).fetchall()
            
            for user in users:
                new_user = User(
                    id=user.id,
                    email=user.email,
                    password_hash=user.password_hash,
                    created_at=user.created_at
                )
                session.add(new_user)
            
            await session.commit()
```

### 2. Data Validation
```python
# scripts/validate_migration.py
async def validate_migration():
    """Validate data consistency after migration"""
    source_engine = create_engine(SQLSERVER_URL)
    
    async with async_session() as session:
        # Validate user count
        source_count = source_engine.execute(
            "SELECT COUNT(*) FROM shared.users"
        ).scalar()
        
        target_count = await session.scalar(
            select(func.count()).select_from(User)
        )
        
        assert source_count == target_count, "User count mismatch"
        
        # Validate data integrity
        sample_users = await session.scalars(
            select(User).limit(100)
        )
        
        for user in sample_users:
            source_user = source_engine.execute(
                "SELECT * FROM shared.users WHERE id = ?",
                user.id
            ).first()
            
            assert user.email == source_user.email, f"Email mismatch for user {user.id}"
```

## Security Implementation

### 1. Row Level Security
```sql
-- Enable RLS
ALTER TABLE dme.equipment ENABLE ROW LEVEL SECURITY;

-- Create Policies
CREATE POLICY equipment_access_policy ON dme.equipment
    FOR ALL
    TO authenticated_users
    USING (
        created_by = current_user_id()
        OR 
        EXISTS (
            SELECT 1 FROM shared.user_roles ur
            WHERE ur.user_id = current_user_id()
            AND ur.role = 'admin'
        )
    );
```

### 2. Data Encryption
```python
# app/core/security.py
from cryptography.fernet import Fernet
from app.core.config import settings

class DataEncryption:
    def __init__(self):
        self.fernet = Fernet(settings.ENCRYPTION_KEY)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        return self.fernet.decrypt(encrypted_data.encode()).decode()
```

## Monitoring and Maintenance

### 1. Database Monitoring
```python
# app/core/monitoring.py
from prometheus_client import Counter, Histogram
from time import time

class DBMetrics:
    query_counter = Counter(
        'db_queries_total',
        'Total number of database queries',
        ['query_type']
    )
    
    query_duration = Histogram(
        'db_query_duration_seconds',
        'Database query duration in seconds',
        ['query_type']
    )
    
    @classmethod
    async def track_query(cls, query_type: str):
        start_time = time()
        try:
            yield
        finally:
            duration = time() - start_time
            cls.query_counter.labels(query_type).inc()
            cls.query_duration.labels(query_type).observe(duration)
```

### 2. Health Checks
```python
# app/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()

@router.get("/health/db")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Test database connection
        await db.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

_Note: This analysis provides a comprehensive overview of our database architecture, migration strategy, and implementation details while maintaining security and performance._
