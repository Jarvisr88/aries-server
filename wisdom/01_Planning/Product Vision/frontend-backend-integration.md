# Frontend-Backend Integration Guide

## Version Compatibility

### Backend Dependencies
```plaintext
FastAPI: 0.104.1
SQLAlchemy: 2.0.23
Pydantic: 2.5.2
Python: 3.9+
```

### Frontend Dependencies
```json
{
  "dependencies": {
    "next": "14.0.3",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "axios": "1.6.2",
    "swr": "2.2.4",
    "@mui/material": "5.14.20",
    "@mui/icons-material": "5.14.19",
    "next-auth": "4.24.5",
    "zod": "3.22.4"
  }
}
```

## Architecture Overview

### API Layer Design
```typescript
// client/lib/api/base.ts
import axios from 'axios';
import { getSession } from 'next-auth/react';

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(async (config) => {
  const session = await getSession();
  if (session?.accessToken) {
    config.headers.Authorization = `Bearer ${session.accessToken}`;
  }
  return config;
});
```

## Type Safety Across Stack

### 1. Shared Types (Pydantic 2.5.2 Compatible)
```typescript
// client/types/api.ts
export interface ApiResponse<T> {
  data: T;
  message?: string;
  metadata?: {
    page?: number;
    totalPages?: number;
    totalItems?: number;
  };
}

// Shared with backend Pydantic models
export interface Equipment {
  id: string;
  name: string;
  category: 'mobility' | 'respiratory' | 'monitoring';
  status: 'available' | 'in-use' | 'maintenance';
  lastMaintenance: string;
  nextMaintenance: string;
}
```

### 2. API Type Generation
```python
# server/app/scripts/generate_types.py
from datamodel_code_generator import generate
from app.schemas import Equipment, Patient, Order

def generate_typescript_types():
    """Generate TypeScript types from Pydantic models"""
    models = [Equipment, Patient, Order]
    
    for model in models:
        generate(
            model.schema_json(),
            output="../../client/types/generated.ts",
            target_python_version="3.9"
        )
```

## FastAPI Integration (0.104.1)

### 1. Backend Routes
```python
# server/app/api/v1/equipment.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.equipment import Equipment, EquipmentCreate
from app.crud.equipment import equipment_crud

router = APIRouter()

@router.get("/{equipment_id}", response_model=Equipment)
async def get_equipment(
    equipment_id: str,
    db: AsyncSession = Depends(get_db)
):
    equipment = await equipment_crud.get(db, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment
```

### 2. SQLAlchemy Models (2.0.23)
```python
# server/app/models/equipment.py
from sqlalchemy import Column, String, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    category = Column(
        Enum('mobility', 'respiratory', 'monitoring', name='equipment_category'),
        nullable=False
    )
    status = Column(
        Enum('available', 'in-use', 'maintenance', name='equipment_status'),
        nullable=False
    )
```

[Rest of the content remains the same...]