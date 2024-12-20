import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.cmn import CMNForm, CMNFormItem
from app.models.order import Order
from app.procedures.mir.update_cmnform import CMNFormMIRUpdater

def test_validate_cmnform_required_fields(db: Session):
    """Test validation of required CMN form fields"""
    form = CMNForm(
        is_active=True
    )
    db.add(form)
    db.commit()
    
    updater = CMNFormMIRUpdater(db)
    issues = updater._validate_cmnform(form)
    
    assert "PhysicianName" in issues
    assert "PhysicianNPI" in issues
    assert "DiagnosisCode" in issues
    assert "StartDate" in issues
    
def test_validate_active_cmnform_checks(db: Session):
    """Test validation of active CMN forms"""
    form = CMNForm(
        physician_name="Dr. Test",
        physician_npi="1234567890",
        diagnosis_code="A123",
        start_date=datetime.now(),
        is_active=True
    )
    db.add(form)
    db.commit()
    
    updater = CMNFormMIRUpdater(db)
    issues = updater._validate_cmnform(form)
    
    assert "NoItems" in issues
    assert "NoPhysicianSignature" in issues
    assert "NoCustomerSignature" in issues
    assert "NoRecentOrders" in issues
    assert "InvalidLengthOfNeed" in issues
    
def test_validate_expired_cmnform(db: Session):
    """Test validation of expired CMN forms"""
    form = CMNForm(
        physician_name="Dr. Test",
        physician_npi="1234567890",
        diagnosis_code="A123",
        start_date=datetime.now() - timedelta(days=400),
        end_date=datetime.now() - timedelta(days=30),
        is_active=True
    )
    db.add(form)
    db.commit()
    
    updater = CMNFormMIRUpdater(db)
    issues = updater._validate_cmnform(form)
    
    assert "Expired" in issues
    
def test_validate_expiring_cmnform(db: Session):
    """Test validation of soon-to-expire CMN forms"""
    form = CMNForm(
        physician_name="Dr. Test",
        physician_npi="1234567890",
        diagnosis_code="A123",
        start_date=datetime.now() - timedelta(days=335),
        end_date=datetime.now() + timedelta(days=15),
        is_active=True
    )
    db.add(form)
    db.commit()
    
    updater = CMNFormMIRUpdater(db)
    issues = updater._validate_cmnform(form)
    
    assert "ExpiringWithin30Days" in issues
    
def test_validate_cmnform_recent_activity(db: Session):
    """Test validation of recent CMN form activity"""
    form = CMNForm(
        physician_name="Dr. Test",
        physician_npi="1234567890",
        diagnosis_code="A123",
        start_date=datetime.now(),
        physician_signature_date=datetime.now(),
        customer_signature_date=datetime.now(),
        length_of_need=12,
        is_active=True
    )
    db.add(form)
    db.flush()
    
    # Add form items
    item = CMNFormItem(
        cmn_form_id=form.id,
        item_description="Test Item"
    )
    db.add(item)
    
    # Add recent order
    order = Order(
        cmn_form_id=form.id,
        order_date=datetime.now()
    )
    db.add(order)
    db.commit()
    
    updater = CMNFormMIRUpdater(db)
    issues = updater._validate_cmnform(form)
    
    assert "NoItems" not in issues
    assert "NoPhysicianSignature" not in issues
    assert "NoCustomerSignature" not in issues
    assert "NoRecentOrders" not in issues
    assert "InvalidLengthOfNeed" not in issues
    
def test_execute_updates_all_forms(db: Session):
    """Test execution of MIR updates for all CMN forms"""
    # Create test forms
    forms = [
        CMNForm(
            physician_name=f"Dr. Test {i}",
            physician_npi="1234567890",
            diagnosis_code="A123",
            start_date=datetime.now(),
            is_active=True
        )
        for i in range(3)
    ]
    db.add_all(forms)
    db.commit()
    
    # Update MIR for all forms
    CMNFormMIRUpdater.execute(db)
    
    # Check that MIR was updated for all forms
    updated_forms = db.query(CMNForm).all()
    assert all(form.mir is not None for form in updated_forms)
    
def test_execute_updates_single_form(db: Session):
    """Test execution of MIR updates for a single CMN form"""
    # Create test forms
    forms = [
        CMNForm(
            physician_name=f"Dr. Test {i}",
            physician_npi="1234567890",
            diagnosis_code="A123",
            start_date=datetime.now(),
            is_active=True
        )
        for i in range(3)
    ]
    db.add_all(forms)
    db.commit()
    
    # Update MIR for single form
    target_id = forms[0].id
    CMNFormMIRUpdater.execute(db, target_id)
    
    # Check that only target form was updated
    updated_forms = db.query(CMNForm).all()
    assert updated_forms[0].mir is not None
    assert all(form.mir is None for form in updated_forms[1:])
