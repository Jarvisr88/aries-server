import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.customer import Customer, CustomerInsurance
from app.models.order import Order
from app.models.invoice import InvoiceTransaction
from app.procedures.mir.update_customer import CustomerMIRUpdater

def test_validate_customer_required_fields(db: Session):
    """Test validation of required customer fields"""
    customer = Customer(
        is_active=True
    )
    db.add(customer)
    db.commit()
    
    updater = CustomerMIRUpdater(db)
    issues = updater._validate_customer(customer)
    
    assert "FirstName" in issues
    assert "LastName" in issues
    assert "Address1" in issues
    assert "City" in issues
    assert "State" in issues
    assert "ZipCode" in issues
    
def test_validate_customer_phone(db: Session):
    """Test validation of customer phone number"""
    customer = Customer(
        first_name="Test",
        last_name="Customer",
        address1="123 Test St",
        city="Test City",
        state="TS",
        zip_code="12345",
        phone="123-456"  # Invalid phone
    )
    db.add(customer)
    db.commit()
    
    updater = CustomerMIRUpdater(db)
    issues = updater._validate_customer(customer)
    
    assert "Phone.Invalid" in issues
    
def test_validate_active_customer_checks(db: Session):
    """Test validation of active customers"""
    customer = Customer(
        first_name="Test",
        last_name="Customer",
        address1="123 Test St",
        city="Test City",
        state="TS",
        zip_code="12345",
        is_active=True
    )
    db.add(customer)
    db.commit()
    
    updater = CustomerMIRUpdater(db)
    issues = updater._validate_customer(customer)
    
    assert "NoActiveInsurance" in issues
    assert "NoRecentOrders" in issues
    assert "NoDOB" in issues
    assert "NoGender" in issues
    
def test_validate_customer_outstanding_balance(db: Session):
    """Test validation of customer outstanding balance"""
    customer = Customer(
        first_name="Test",
        last_name="Customer",
        address1="123 Test St",
        city="Test City",
        state="TS",
        zip_code="12345",
        is_active=True
    )
    db.add(customer)
    db.flush()
    
    # Add old unpaid transaction
    transaction = InvoiceTransaction(
        customer_id=customer.id,
        transaction_date=datetime.now() - timedelta(days=100),
        amount=100,
        is_paid=False
    )
    db.add(transaction)
    db.commit()
    
    updater = CustomerMIRUpdater(db)
    issues = updater._validate_customer(customer)
    
    assert "OutstandingBalance" in issues
    
def test_validate_customer_recent_activity(db: Session):
    """Test validation of recent customer activity"""
    customer = Customer(
        first_name="Test",
        last_name="Customer",
        address1="123 Test St",
        city="Test City",
        state="TS",
        zip_code="12345",
        is_active=True,
        date_of_birth=datetime(1990, 1, 1),
        gender="M"
    )
    db.add(customer)
    db.flush()
    
    # Add active insurance
    insurance = CustomerInsurance(
        customer_id=customer.id,
        is_active=True
    )
    db.add(insurance)
    
    # Add recent order
    order = Order(
        customer_id=customer.id,
        order_date=datetime.now()
    )
    db.add(order)
    db.commit()
    
    updater = CustomerMIRUpdater(db)
    issues = updater._validate_customer(customer)
    
    assert "NoActiveInsurance" not in issues
    assert "NoRecentOrders" not in issues
    assert "NoDOB" not in issues
    assert "NoGender" not in issues
    
def test_execute_updates_all_customers(db: Session):
    """Test execution of MIR updates for all customers"""
    # Create test customers
    customers = [
        Customer(
            first_name=f"Test{i}",
            last_name="Customer",
            address1="123 Test St",
            city="Test City",
            state="TS",
            zip_code="12345",
            is_active=True
        )
        for i in range(3)
    ]
    db.add_all(customers)
    db.commit()
    
    # Update MIR for all customers
    CustomerMIRUpdater.execute(db)
    
    # Check that MIR was updated for all customers
    updated_customers = db.query(Customer).all()
    assert all(customer.mir is not None for customer in updated_customers)
    
def test_execute_updates_single_customer(db: Session):
    """Test execution of MIR updates for a single customer"""
    # Create test customers
    customers = [
        Customer(
            first_name=f"Test{i}",
            last_name="Customer",
            address1="123 Test St",
            city="Test City",
            state="TS",
            zip_code="12345",
            is_active=True
        )
        for i in range(3)
    ]
    db.add_all(customers)
    db.commit()
    
    # Update MIR for single customer
    target_id = customers[0].id
    CustomerMIRUpdater.execute(db, target_id)
    
    # Check that only target customer was updated
    updated_customers = db.query(Customer).all()
    assert updated_customers[0].mir is not None
    assert all(customer.mir is None for customer in updated_customers[1:])
