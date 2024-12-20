# C# to Python Migration Template

## Migration Checklist

### 1. Data Layer Migration
- [ ] Identify all Entity Framework models
- [ ] Create equivalent SQLAlchemy models
- [ ] Map relationships and constraints
- [ ] Create Alembic migrations
- [ ] Validate data types and conversions
- [ ] Test data integrity

### 2. Business Logic Migration
- [ ] Map C# services to Python services
- [ ] Convert dependency injection patterns
- [ ] Migrate business rules and validation
- [ ] Implement async patterns
- [ ] Test business logic equivalence

### 3. API Layer Migration
- [ ] Convert controllers to FastAPI routes
- [ ] Implement request/response models
- [ ] Set up authentication/authorization
- [ ] Document API endpoints
- [ ] Test API functionality

## Code Migration Templates

### 1. Entity Framework to SQLAlchemy
```csharp
// C# Entity
public class Customer
{
    public Guid Id { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
    public virtual ICollection<Order> Orders { get; set; }
}
```

```python
# Python SQLAlchemy Model
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    orders = relationship("Order", back_populates="customer")
```

### 2. Service Layer
```csharp
// C# Service
public class CustomerService : ICustomerService
{
    private readonly ICustomerRepository _repository;
    
    public CustomerService(ICustomerRepository repository)
    {
        _repository = repository;
    }
    
    public async Task<Customer> CreateCustomerAsync(CustomerDto dto)
    {
        var customer = new Customer
        {
            Name = dto.Name,
            Email = dto.Email
        };
        
        return await _repository.AddAsync(customer);
    }
}
```

```python
# Python Service
from fastapi import Depends
from app.crud.customer import customer_crud
from app.schemas.customer import CustomerCreate, Customer

class CustomerService:
    def __init__(self, crud=Depends(customer_crud)):
        self.crud = crud
    
    async def create_customer(
        self,
        data: CustomerCreate,
        db: AsyncSession
    ) -> Customer:
        return await self.crud.create(db, data)
```

### 3. Controller to FastAPI Route
```csharp
// C# Controller
[ApiController]
[Route("api/[controller]")]
public class CustomersController : ControllerBase
{
    private readonly ICustomerService _service;
    
    [HttpPost]
    public async Task<ActionResult<CustomerDto>> Create(CreateCustomerDto dto)
    {
        var customer = await _service.CreateCustomerAsync(dto);
        return Ok(customer);
    }
}
```

```python
# FastAPI Route
from fastapi import APIRouter, Depends
from app.services.customer import CustomerService
from app.schemas.customer import CustomerCreate, Customer

router = APIRouter()

@router.post("/", response_model=Customer)
async def create_customer(
    data: CustomerCreate,
    service: CustomerService = Depends()
):
    return await service.create_customer(data)
```

### 4. DTOs to Pydantic Models
```csharp
// C# DTO
public class CreateCustomerDto
{
    [Required]
    [StringLength(100)]
    public string Name { get; set; }
    
    [Required]
    [EmailAddress]
    public string Email { get; set; }
}
```

```python
# Pydantic Schema
from pydantic import BaseModel, EmailStr, Field

class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
```

### 5. Authentication/Authorization
```csharp
// C# Auth
[Authorize]
public class SecureController : ControllerBase
{
    [HttpGet]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult> SecureEndpoint()
    {
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        // Implementation
    }
}
```

```python
# FastAPI Auth
from fastapi import Depends, Security
from app.core.auth import get_current_user, require_roles

@router.get("/secure")
async def secure_endpoint(
    current_user: User = Security(
        get_current_user,
        scopes=["admin"]
    )
):
    # Implementation
    pass
```

### 6. Exception Handling
```csharp
// C# Exception
public class NotFoundException : Exception
{
    public NotFoundException(string message)
        : base(message)
    {
    }
}

// Exception Handler
app.UseExceptionHandler(builder =>
{
    builder.Run(async context =>
    {
        var exception = context.Features.Get<IExceptionHandlerFeature>();
        // Handle exception
    });
});
```

```python
# FastAPI Exception
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request

class NotFoundException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=404, detail=detail)

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(
    request: Request,
    exc: NotFoundException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
```

### 7. Dependency Injection
```csharp
// C# DI
services.AddScoped<ICustomerService, CustomerService>();
services.AddScoped<ICustomerRepository, CustomerRepository>();
```

```python
# FastAPI DI
from fastapi import Depends
from app.db.session import get_db
from app.crud.customer import CustomerCRUD
from app.services.customer import CustomerService

def get_customer_crud():
    return CustomerCRUD()

def get_customer_service(
    crud: CustomerCRUD = Depends(get_customer_crud)
):
    return CustomerService(crud)
```

## Testing Templates

### 1. Unit Tests
```python
# tests/services/test_customer.py
import pytest
from app.services.customer import CustomerService
from app.schemas.customer import CustomerCreate

@pytest.mark.asyncio
async def test_create_customer(db_session):
    service = CustomerService()
    data = CustomerCreate(
        name="Test Customer",
        email="test@example.com"
    )
    
    customer = await service.create_customer(data, db_session)
    assert customer.name == data.name
    assert customer.email == data.email
```

### 2. Integration Tests
```python
# tests/api/test_customer.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_customer_api(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/customers",
        json={
            "name": "Test Customer",
            "email": "test@example.com"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Customer"
```

## Migration Scripts

### 1. Data Migration
```python
# scripts/migrate_data.py
import asyncio
from app.db.session import async_session
from app.models import Customer
from legacy_db import LegacyDB

async def migrate_customers():
    async with async_session() as session:
        legacy_data = LegacyDB.fetch_all_customers()
        
        for item in legacy_data:
            customer = Customer(
                id=item.Id,
                name=item.Name,
                email=item.Email
            )
            session.add(customer)
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(migrate_customers())
```

### 2. Schema Migration
```python
# alembic/versions/xxx_create_customers.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'customers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

def downgrade():
    op.drop_table('customers')
```

_Note: This template provides a structured approach for migrating different components of a C# application to our Python stack. Customize the templates based on specific requirements while maintaining consistency with our architecture._
