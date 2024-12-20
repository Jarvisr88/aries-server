# Stored Procedures Analysis and Migration

## SQL Server to PostgreSQL Migration

### 1. Function Translation Patterns

#### Complex Calculations
```sql
-- SQL Server Stored Procedure
CREATE PROCEDURE dme.CalculateEquipmentUtilization
    @StartDate DateTime,
    @EndDate DateTime
AS
BEGIN
    SELECT 
        e.id,
        e.name,
        COUNT(mr.id) as maintenance_count,
        DATEDIFF(day, @StartDate, @EndDate) as total_days,
        CAST(COUNT(mr.id) AS FLOAT) / DATEDIFF(day, @StartDate, @EndDate) as utilization_rate
    FROM dme.equipment e
    LEFT JOIN dme.maintenance_records mr 
        ON e.id = mr.equipment_id
        AND mr.maintenance_date BETWEEN @StartDate AND @EndDate
    GROUP BY e.id, e.name;
END;

-- PostgreSQL Function
CREATE OR REPLACE FUNCTION dme.calculate_equipment_utilization(
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ
)
RETURNS TABLE (
    id UUID,
    name VARCHAR,
    maintenance_count BIGINT,
    total_days INTEGER,
    utilization_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.name,
        COUNT(mr.id)::BIGINT as maintenance_count,
        EXTRACT(DAY FROM end_date - start_date)::INTEGER as total_days,
        COALESCE(
            COUNT(mr.id)::NUMERIC / NULLIF(EXTRACT(DAY FROM end_date - start_date), 0),
            0
        ) as utilization_rate
    FROM dme.equipment e
    LEFT JOIN dme.maintenance_records mr 
        ON e.id = mr.equipment_id
        AND mr.maintenance_date BETWEEN start_date AND end_date
    GROUP BY e.id, e.name;
END;
$$ LANGUAGE plpgsql;
```

### 2. FastAPI Implementation

#### Service Layer
```python
# app/services/equipment.py
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class EquipmentAnalyticsService:
    async def calculate_utilization(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ):
        query = """
        SELECT * FROM dme.calculate_equipment_utilization(
            :start_date,
            :end_date
        )
        """
        
        result = await db.execute(
            text(query),
            {
                'start_date': start_date,
                'end_date': end_date
            }
        )
        return result.mappings().all()
```

#### API Endpoint
```python
# app/api/v1/analytics.py
from fastapi import APIRouter, Depends
from datetime import datetime
from app.services.equipment import EquipmentAnalyticsService
from app.core.deps import get_db

router = APIRouter()

@router.get("/equipment/utilization")
async def get_equipment_utilization(
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_db),
    service: EquipmentAnalyticsService = Depends()
):
    return await service.calculate_utilization(
        db,
        start_date,
        end_date
    )
```

## Complex Business Logic Migration

### 1. Inventory Management
```sql
-- SQL Server
CREATE PROCEDURE dme.UpdateInventoryStatus
    @EquipmentId UNIQUEIDENTIFIER,
    @NewStatus NVARCHAR(50),
    @UserId UNIQUEIDENTIFIER
AS
BEGIN
    BEGIN TRANSACTION;
    
    DECLARE @CurrentStatus NVARCHAR(50);
    
    SELECT @CurrentStatus = status
    FROM dme.equipment
    WHERE id = @EquipmentId;
    
    IF @CurrentStatus IS NULL
        THROW 50404, 'Equipment not found', 1;
        
    IF @CurrentStatus = @NewStatus
        RETURN;
        
    UPDATE dme.equipment
    SET 
        status = @NewStatus,
        updated_at = GETDATE(),
        updated_by = @UserId
    WHERE id = @EquipmentId;
    
    INSERT INTO dme.status_history (
        equipment_id,
        previous_status,
        new_status,
        changed_by,
        changed_at
    ) VALUES (
        @EquipmentId,
        @CurrentStatus,
        @NewStatus,
        @UserId,
        GETDATE()
    );
    
    COMMIT;
END;

-- PostgreSQL Function
CREATE OR REPLACE FUNCTION dme.update_inventory_status(
    equipment_id UUID,
    new_status VARCHAR,
    user_id UUID
)
RETURNS TABLE (
    id UUID,
    status VARCHAR,
    updated_at TIMESTAMPTZ
) AS $$
DECLARE
    current_status VARCHAR;
BEGIN
    -- Get current status
    SELECT status INTO current_status
    FROM dme.equipment
    WHERE id = equipment_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Equipment not found'
            USING ERRCODE = 'P0002';
    END IF;
    
    IF current_status = new_status THEN
        RETURN QUERY
        SELECT e.id, e.status, e.updated_at
        FROM dme.equipment e
        WHERE e.id = equipment_id;
        RETURN;
    END IF;
    
    -- Update equipment status
    UPDATE dme.equipment
    SET 
        status = new_status,
        updated_at = CURRENT_TIMESTAMP,
        updated_by = user_id
    WHERE id = equipment_id;
    
    -- Record status change
    INSERT INTO dme.status_history (
        equipment_id,
        previous_status,
        new_status,
        changed_by,
        changed_at
    ) VALUES (
        equipment_id,
        current_status,
        new_status,
        user_id,
        CURRENT_TIMESTAMP
    );
    
    RETURN QUERY
    SELECT e.id, e.status, e.updated_at
    FROM dme.equipment e
    WHERE e.id = equipment_id;
END;
$$ LANGUAGE plpgsql;
```

### 2. FastAPI Implementation
```python
# app/services/inventory.py
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.equipment import Equipment, StatusHistory
from app.schemas.equipment import EquipmentStatus

class InventoryService:
    async def update_status(
        self,
        db: AsyncSession,
        equipment_id: UUID,
        new_status: EquipmentStatus,
        user_id: UUID
    ) -> Equipment:
        async with db.begin():
            # Get current equipment
            equipment = await db.get(Equipment, equipment_id)
            if not equipment:
                raise HTTPException(
                    status_code=404,
                    detail="Equipment not found"
                )
            
            if equipment.status == new_status:
                return equipment
            
            # Record previous status
            previous_status = equipment.status
            
            # Update equipment
            equipment.status = new_status
            equipment.updated_by = user_id
            
            # Record status change
            status_history = StatusHistory(
                equipment_id=equipment_id,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=user_id
            )
            
            db.add(status_history)
            await db.commit()
            await db.refresh(equipment)
            
            return equipment
```

## Performance Optimization

### 1. Batch Processing
```sql
-- PostgreSQL Function
CREATE OR REPLACE FUNCTION dme.batch_update_equipment_status(
    equipment_ids UUID[],
    new_status VARCHAR,
    user_id UUID
)
RETURNS SETOF dme.equipment AS $$
DECLARE
    equipment_id UUID;
BEGIN
    FOREACH equipment_id IN ARRAY equipment_ids
    LOOP
        -- Update each equipment
        UPDATE dme.equipment
        SET 
            status = new_status,
            updated_at = CURRENT_TIMESTAMP,
            updated_by = user_id
        WHERE id = equipment_id
        RETURNING *;
        
        -- Record status changes
        INSERT INTO dme.status_history (
            equipment_id,
            new_status,
            changed_by
        )
        SELECT 
            id,
            new_status,
            user_id
        FROM dme.equipment
        WHERE id = equipment_id;
    END LOOP;
    
    RETURN QUERY
    SELECT * FROM dme.equipment
    WHERE id = ANY(equipment_ids);
END;
$$ LANGUAGE plpgsql;
```

### 2. Async Implementation
```python
# app/services/batch.py
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentStatus

class BatchService:
    async def update_equipment_status(
        self,
        db: AsyncSession,
        equipment_ids: List[UUID],
        new_status: EquipmentStatus,
        user_id: UUID
    ) -> List[Equipment]:
        query = """
        SELECT * FROM dme.batch_update_equipment_status(
            :equipment_ids,
            :new_status,
            :user_id
        )
        """
        
        result = await db.execute(
            text(query),
            {
                'equipment_ids': equipment_ids,
                'new_status': new_status.value,
                'user_id': user_id
            }
        )
        
        return result.scalars().all()
```

## Error Handling

### 1. Custom Exceptions
```python
# app/core/exceptions.py
class InventoryException(Exception):
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(message)

class StatusTransitionError(InventoryException):
    def __init__(self, message: str):
        super().__init__(
            message,
            code='invalid_status_transition'
        )
```

### 2. Error Handlers
```python
# app/api/v1/inventory.py
@router.put("/equipment/{equipment_id}/status")
async def update_equipment_status(
    equipment_id: UUID,
    new_status: EquipmentStatus,
    current_user: User = Depends(get_current_user),
    service: InventoryService = Depends()
):
    try:
        return await service.update_status(
            equipment_id,
            new_status,
            current_user.id
        )
    except StatusTransitionError as e:
        raise HTTPException(
            status_code=400,
            detail={
                'message': str(e),
                'code': e.code
            }
        )
```

## Testing Strategy

### 1. Function Tests
```python
# tests/functions/test_inventory.py
import pytest
from app.services.inventory import InventoryService
from app.schemas.equipment import EquipmentStatus

@pytest.mark.asyncio
async def test_update_equipment_status(
    db_session,
    test_equipment,
    test_user
):
    service = InventoryService()
    
    updated = await service.update_status(
        db_session,
        test_equipment.id,
        EquipmentStatus.MAINTENANCE,
        test_user.id
    )
    
    assert updated.status == EquipmentStatus.MAINTENANCE
    
    # Verify history
    history = await db_session.scalars(
        select(StatusHistory)
        .where(StatusHistory.equipment_id == test_equipment.id)
        .order_by(StatusHistory.changed_at.desc())
    )
    
    latest = history.first()
    assert latest.previous_status == test_equipment.status
    assert latest.new_status == EquipmentStatus.MAINTENANCE
```

### 2. Integration Tests
```python
# tests/api/test_inventory.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_batch_update_status(
    async_client: AsyncClient,
    test_equipment_batch,
    test_user_token
):
    response = await async_client.put(
        "/api/v1/inventory/batch/status",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "equipment_ids": [str(e.id) for e in test_equipment_batch],
            "new_status": "maintenance"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(test_equipment_batch)
    assert all(e["status"] == "maintenance" for e in data)
```

_Note: This analysis provides a comprehensive guide for migrating stored procedures to our new stack while maintaining functionality and adding modern features like async operations and proper error handling._
