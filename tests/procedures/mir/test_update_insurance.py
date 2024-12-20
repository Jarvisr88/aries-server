import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.insurance import InsuranceCompany, InsuranceCompanyEDI
from app.models.customer import CustomerInsurance
from app.models.invoice import InvoiceTransaction
from app.procedures.mir.update_insurance import InsuranceCompanyMIRUpdater

def test_validate_insurance_required_fields(db: Session):
    """Test validation of required insurance fields"""
    insurance = InsuranceCompany(
        is_active=True
    )
    db.add(insurance)
    db.commit()
    
    updater = InsuranceCompanyMIRUpdater(db)
    issues = updater._validate_insurance(insurance)
    
    assert "Name" in issues
    assert "Address1" in issues
    assert "City" in issues
    assert "State" in issues
    assert "ZipCode" in issues
    
def test_validate_insurance_phone(db: Session):
    """Test validation of insurance phone number"""
    insurance = InsuranceCompany(
        name="Test Insurance",
        address1="123 Test St",
        city="Test City",
        state="TS",
        zip_code="12345",
        phone="123-456"  # Invalid phone
    )
    db.add(insurance)
    db.commit()
    
    updater = InsuranceCompanyMIRUpdater(db)
    issues = updater._validate_insurance(insurance)
    
    assert "Phone.Invalid" in issues
    
def test_validate_active_insurance_checks(db: Session):
    """Test validation of active insurance companies"""
    insurance = InsuranceCompany(
        name="Test Insurance",
        address1="123 Test St",
        city="Test City",
        state="TS",
        zip_code="12345",
        is_active=True,
        is_electronic_payer=True
    )
    db.add(insurance)
    db.commit()
    
    updater = InsuranceCompanyMIRUpdater(db)
    issues = updater._validate_insurance(insurance)
    
    assert "NoActiveCustomers" in issues
    assert "NoRecentPayments" in issues
    assert "NoEDIConfig" in issues
    
def test_validate_insurance_edi_config(db: Session):
    """Test validation of EDI configuration"""
    insurance = InsuranceCompany(
        name="Test Insurance",
        address1="123 Test St",
        city="Test City",
        state="TS",
        zip_code="12345",
        is_active=True,
        is_electronic_payer=True
    )
    db.add(insurance)
    db.flush()
    
    edi_config = InsuranceCompanyEDI(
        insurance_company_id=insurance.id
    )
    db.add(edi_config)
    db.commit()
    
    updater = InsuranceCompanyMIRUpdater(db)
    issues = updater._validate_insurance(insurance)
    
    assert "NoPayerID" in issues
    assert "NoReceiverID" in issues
    
def test_validate_insurance_recent_activity(db: Session):
    """Test validation of recent insurance activity"""
    insurance = InsuranceCompany(
        name="Test Insurance",
        address1="123 Test St",
        city="Test City",
        state="TS",
        zip_code="12345",
        is_active=True
    )
    db.add(insurance)
    db.flush()
    
    # Add active customer insurance
    customer_insurance = CustomerInsurance(
        insurance_company_id=insurance.id,
        is_active=True
    )
    db.add(customer_insurance)
    
    # Add recent payment
    payment = InvoiceTransaction(
        insurance_company_id=insurance.id,
        transaction_date=datetime.now(),
        amount=100
    )
    db.add(payment)
    db.commit()
    
    updater = InsuranceCompanyMIRUpdater(db)
    issues = updater._validate_insurance(insurance)
    
    assert "NoActiveCustomers" not in issues
    assert "NoRecentPayments" not in issues
    
def test_execute_updates_all_companies(db: Session):
    """Test execution of MIR updates for all insurance companies"""
    # Create test companies
    companies = [
        InsuranceCompany(
            name=f"Test Insurance {i}",
            address1="123 Test St",
            city="Test City",
            state="TS",
            zip_code="12345",
            is_active=True
        )
        for i in range(3)
    ]
    db.add_all(companies)
    db.commit()
    
    # Update MIR for all companies
    InsuranceCompanyMIRUpdater.execute(db)
    
    # Check that MIR was updated for all companies
    updated_companies = db.query(InsuranceCompany).all()
    assert all(company.mir is not None for company in updated_companies)
    
def test_execute_updates_single_company(db: Session):
    """Test execution of MIR updates for a single insurance company"""
    # Create test companies
    companies = [
        InsuranceCompany(
            name=f"Test Insurance {i}",
            address1="123 Test St",
            city="Test City",
            state="TS",
            zip_code="12345",
            is_active=True
        )
        for i in range(3)
    ]
    db.add_all(companies)
    db.commit()
    
    # Update MIR for single company
    target_id = companies[0].id
    InsuranceCompanyMIRUpdater.execute(db, target_id)
    
    # Check that only target company was updated
    updated_companies = db.query(InsuranceCompany).all()
    assert updated_companies[0].mir is not None
    assert all(company.mir is None for company in updated_companies[1:])
