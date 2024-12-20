# Aries Enterprise System Architecture

## 1. System Overview

### 1.1 Purpose
Aries Enterprise is a comprehensive medical equipment management and billing system designed to handle complex workflows around inventory management, order processing, and medical billing.

### 1.2 Technology Stack
- **Backend Framework**: FastAPI with Python 3.9+
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy with async support
- **API Style**: RESTful with async/await patterns
- **Authentication**: Token-based (implementation details pending)

## 2. Core Domains

### 2.1 Invoice Management
#### 2.1.1 Components
- **Invoice Processing**
  - Balance calculations
  - Internal reflagging
  - Writeoff handling
  - Transaction history
  - Insurance submission tracking
  
#### 2.1.2 Key Classes
- `InvoiceBalanceUpdater`: Updates invoice balances based on details
- `InvoiceInternalReflag`: Handles internal reflagging
- `InvoiceDetailsInternalWriteoff`: Processes writeoffs
- `InvoicePendingSubmissionsUpdater`: Manages insurance submissions

### 2.2 Inventory Management
#### 2.2.1 Components
- **Serial Number Tracking**
  - Status tracking
  - Warehouse transfers
  - Transaction history
  
#### 2.2.2 Key Classes
- `SerialTransfer`: Handles warehouse transfers
- `SerialRefresh`: Updates serial status
- `InventoryRefresh`: Maintains inventory quantities
- `InventoryPORefresh`: Refreshes inventory from POs

### 2.3 Order Processing
#### 2.3.1 Components
- **Date of Service (DOS) Management**
  - Period calculations
  - Billing cycle handling
  - Quantity conversions

#### 2.3.2 Key Classes
- `OrderDOSUtils`: Date calculations and validations
- `QuantityConverters`: Billing quantity calculations

### 2.4 Medical Information Records
#### 2.4.1 Components
- **MIR Field Management**
  - Validation rules
  - Required field tracking
  - Update procedures

#### 2.4.2 Key Classes
- `FacilityMIRUpdater`: Updates facility MIR fields
- `DoctorMIRUpdater`: Updates doctor MIR fields

## 3. Data Models

### 3.1 Invoice Domain
```python
class Invoice:
    id: int
    customer_id: int
    balance: Decimal
    status: str
    transactions: List[InvoiceTransaction]
    details: List[InvoiceDetail]

class InvoiceTransaction:
    id: int
    invoice_id: int
    amount: Decimal
    transaction_type: str
    transaction_date: datetime
```

### 3.2 Inventory Domain
```python
class Serial:
    id: int
    inventory_item_id: int
    status: str
    warehouse_id: int
    transactions: List[SerialTransaction]

class InventoryItem:
    id: int
    name: str
    quantity: int
    warehouse_id: int
```

## 4. Business Rules

### 4.1 Billing Periods
- **Supported Periods**:
  - One Time
  - Daily
  - Weekly
  - Monthly (Calendar and Rolling)
  - Quarterly
  - Semi-Annually
  - Annually
  - Custom

### 4.2 Quantity Calculations
```python
# Conversion Multipliers
DAILY_TO_WEEKLY = 7.0
WEEKLY_TO_MONTHLY = 4.0
MONTHLY_TO_QUARTERLY = 3.0
QUARTERLY_TO_ANNUAL = 4.0
```

### 4.3 Validation Rules
- NPI must be 10 digits
- Required MIR fields per entity type
- Balance validation thresholds

## 5. Integration Points

### 5.1 External Systems
- Medical Records Systems (via MIR)
- Billing Systems
- Inventory Management Systems

### 5.2 Internal Services
- Transaction Processing
- Reporting Services
- Audit Trail System

## 6. Security

### 6.1 Authentication
- Token-based authentication
- Role-based access control

### 6.2 Audit Trail
- User tracking on all transactions
- Change history logging
- Transaction verification

## 7. Performance Considerations

### 7.1 Database
- Async operations for better scalability
- Efficient query patterns using SQLAlchemy
- Transaction management for data integrity

### 7.2 API
- Async/await patterns
- Proper error handling
- Response caching where appropriate

## 8. Development Guidelines

### 8.1 Code Organization
```
server/
  app/
    procedures/
      invoice/
      inventory/
      order/
      serial/
    models/
    services/
    api/
```

### 8.2 Best Practices
- Type hints for better IDE support
- Comprehensive docstrings
- Unit test coverage
- Error handling patterns

## 9. Deployment

### 9.1 Requirements
- Python 3.9+
- PostgreSQL
- FastAPI
- SQLAlchemy

### 9.2 Configuration
- Environment-based settings
- Logging configuration
- Database connection pooling

---
*Note: This specification is based on stored procedure implementations and will be updated as more procedures are converted.*
