# Database Relationships Analysis

## Core Entity Relationships

### 1. User Management
```sql
-- Users and Roles
CREATE TABLE shared.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shared.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE shared.user_roles (
    user_id UUID REFERENCES shared.users(id),
    role_id UUID REFERENCES shared.roles(id),
    PRIMARY KEY (user_id, role_id)
);
```

### 2. Equipment Management
```sql
-- Equipment and Maintenance
CREATE TABLE dme.equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category equipment_category NOT NULL,
    status equipment_status NOT NULL,
    created_by UUID REFERENCES shared.users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dme.maintenance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID REFERENCES dme.equipment(id),
    performed_by UUID REFERENCES shared.users(id),
    maintenance_date TIMESTAMPTZ NOT NULL,
    notes TEXT,
    next_maintenance TIMESTAMPTZ
);
```

## SQLAlchemy Relationship Mapping

### 1. Base Models
```python
# app/models/base.py
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

### 2. User Models
```python
# app/models/user.py
class User(BaseModel):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'shared'}
    
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Relationships
    roles = relationship(
        'Role',
        secondary='shared.user_roles',
        back_populates='users'
    )
    created_equipment = relationship(
        'Equipment',
        back_populates='created_by_user'
    )
    maintenance_records = relationship(
        'MaintenanceRecord',
        back_populates='performed_by_user'
    )

class Role(BaseModel):
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'shared'}
    
    name = Column(String(50), unique=True, nullable=False)
    
    # Relationships
    users = relationship(
        'User',
        secondary='shared.user_roles',
        back_populates='roles'
    )
```

### 3. Equipment Models
```python
# app/models/equipment.py
class Equipment(BaseModel):
    __tablename__ = 'equipment'
    __table_args__ = {'schema': 'dme'}
    
    name = Column(String(255), nullable=False)
    category = Column(Enum(EquipmentCategory), nullable=False)
    status = Column(Enum(EquipmentStatus), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('shared.users.id'))
    
    # Relationships
    created_by_user = relationship(
        'User',
        back_populates='created_equipment'
    )
    maintenance_records = relationship(
        'MaintenanceRecord',
        back_populates='equipment',
        cascade='all, delete-orphan'
    )

class MaintenanceRecord(BaseModel):
    __tablename__ = 'maintenance_records'
    __table_args__ = {'schema': 'dme'}
    
    equipment_id = Column(UUID(as_uuid=True), ForeignKey('dme.equipment.id'))
    performed_by = Column(UUID(as_uuid=True), ForeignKey('shared.users.id'))
    maintenance_date = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text)
    next_maintenance = Column(DateTime(timezone=True))
    
    # Relationships
    equipment = relationship(
        'Equipment',
        back_populates='maintenance_records'
    )
    performed_by_user = relationship(
        'User',
        back_populates='maintenance_records'
    )
```

## Relationship Queries

### 1. Eager Loading
```python
# app/crud/equipment.py
async def get_equipment_with_maintenance(
    db: AsyncSession,
    equipment_id: UUID
) -> Optional[Equipment]:
    query = (
        select(Equipment)
        .options(
            joinedload(Equipment.maintenance_records)
            .joinedload(MaintenanceRecord.performed_by_user),
            joinedload(Equipment.created_by_user)
        )
        .where(Equipment.id == equipment_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

### 2. Relationship Operations
```python
# app/services/equipment.py
class EquipmentService:
    async def add_maintenance_record(
        self,
        db: AsyncSession,
        equipment_id: UUID,
        user_id: UUID,
        data: MaintenanceRecordCreate
    ) -> MaintenanceRecord:
        equipment = await self.get_equipment(db, equipment_id)
        if not equipment:
            raise NotFoundException("Equipment not found")
            
        record = MaintenanceRecord(
            equipment_id=equipment_id,
            performed_by=user_id,
            maintenance_date=data.maintenance_date,
            notes=data.notes,
            next_maintenance=data.next_maintenance
        )
        
        db.add(record)
        await db.commit()
        await db.refresh(record)
        
        return record
```

## Cascade Operations

### 1. Delete Operations
```python
# app/crud/base.py
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    async def remove(
        self,
        db: AsyncSession,
        id: UUID
    ) -> bool:
        obj = await db.get(self.model, id)
        if not obj:
            return False
            
        await db.delete(obj)
        await db.commit()
        return True
```

### 2. Bulk Operations
```python
# app/services/maintenance.py
class MaintenanceService:
    async def bulk_update_maintenance_dates(
        self,
        db: AsyncSession,
        equipment_ids: List[UUID],
        next_maintenance: datetime
    ) -> List[Equipment]:
        stmt = (
            update(Equipment)
            .where(Equipment.id.in_(equipment_ids))
            .values(next_maintenance=next_maintenance)
            .returning(Equipment)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalars().all()
```

## Data Validation

### 1. Pydantic Models
```python
# app/schemas/equipment.py
class MaintenanceRecordCreate(BaseModel):
    maintenance_date: datetime
    notes: Optional[str]
    next_maintenance: Optional[datetime]
    
    @validator('next_maintenance')
    def validate_next_maintenance(cls, v, values):
        if v and v <= values['maintenance_date']:
            raise ValueError(
                'Next maintenance must be after maintenance date'
            )
        return v

class EquipmentWithMaintenance(BaseModel):
    id: UUID
    name: str
    category: EquipmentCategory
    status: EquipmentStatus
    maintenance_records: List[MaintenanceRecord]
    
    class Config:
        from_attributes = True
```

### 2. Database Constraints
```sql
-- Check Constraints
ALTER TABLE dme.maintenance_records
ADD CONSTRAINT valid_maintenance_dates
CHECK (next_maintenance > maintenance_date);

-- Foreign Key Constraints
ALTER TABLE dme.maintenance_records
ADD CONSTRAINT fk_equipment
FOREIGN KEY (equipment_id)
REFERENCES dme.equipment(id)
ON DELETE CASCADE;
```

## Performance Optimization

### 1. Indexing Strategy
```sql
-- Relationship Indexes
CREATE INDEX idx_maintenance_equipment
ON dme.maintenance_records(equipment_id);

CREATE INDEX idx_maintenance_user
ON dme.maintenance_records(performed_by);

CREATE INDEX idx_user_roles
ON shared.user_roles(user_id, role_id);
```

### 2. Query Optimization
```python
# app/crud/equipment.py
async def get_equipment_summary(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[Dict]:
    query = """
    SELECT 
        e.id,
        e.name,
        e.category,
        e.status,
        COUNT(mr.id) as maintenance_count,
        MAX(mr.maintenance_date) as last_maintenance
    FROM dme.equipment e
    LEFT JOIN dme.maintenance_records mr ON e.id = mr.equipment_id
    GROUP BY e.id, e.name, e.category, e.status
    ORDER BY e.name
    OFFSET :skip LIMIT :limit
    """
    
    result = await db.execute(
        text(query),
        {'skip': skip, 'limit': limit}
    )
    return result.mappings().all()
```

_Note: This analysis provides a comprehensive overview of database relationships, their implementation in SQLAlchemy, and optimization strategies while maintaining data integrity and performance._
