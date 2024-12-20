import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.invoice import Invoice, InvoiceTransaction, InvoiceTransactionType
from app.models.payment import Payment, PaymentMethod
from app.models.customer import Customer
from app.procedures.invoice.retail_add_payments import RetailInvoicePaymentAdder
from app.core.exceptions import ProcedureError

def test_validate_payment_invalid_invoice(db: Session):
    """Test validation with invalid invoice"""
    adder = RetailInvoicePaymentAdder(db)
    
    with pytest.raises(ProcedureError, match="Invoice not found"):
        adder._validate_payment(None, Decimal("100.00"), "Cash")
        
def test_validate_payment_non_retail_invoice(db: Session):
    """Test validation with non-retail invoice"""
    invoice = Invoice(
        is_retail=False,
        balance=Decimal("100.00")
    )
    db.add(invoice)
    db.commit()
    
    adder = RetailInvoicePaymentAdder(db)
    
    with pytest.raises(ProcedureError, match="Payment can only be added to retail invoices"):
        adder._validate_payment(invoice, Decimal("50.00"), "Cash")
        
def test_validate_payment_negative_amount(db: Session):
    """Test validation with negative payment amount"""
    invoice = Invoice(
        is_retail=True,
        balance=Decimal("100.00")
    )
    db.add(invoice)
    db.commit()
    
    adder = RetailInvoicePaymentAdder(db)
    
    with pytest.raises(ProcedureError, match="Payment amount must be positive"):
        adder._validate_payment(invoice, Decimal("-50.00"), "Cash")
        
def test_validate_payment_exceeds_balance(db: Session):
    """Test validation with payment exceeding balance"""
    invoice = Invoice(
        is_retail=True,
        balance=Decimal("100.00")
    )
    db.add(invoice)
    db.commit()
    
    adder = RetailInvoicePaymentAdder(db)
    
    with pytest.raises(ProcedureError, match="Payment amount cannot exceed invoice balance"):
        adder._validate_payment(invoice, Decimal("150.00"), "Cash")
        
def test_validate_payment_invalid_method(db: Session):
    """Test validation with invalid payment method"""
    invoice = Invoice(
        is_retail=True,
        balance=Decimal("100.00")
    )
    db.add(invoice)
    db.commit()
    
    adder = RetailInvoicePaymentAdder(db)
    
    with pytest.raises(ProcedureError, match="Invalid payment method"):
        adder._validate_payment(invoice, Decimal("50.00"), "InvalidMethod")
        
def test_validate_payment_missing_reference(db: Session):
    """Test validation with missing required reference"""
    invoice = Invoice(
        is_retail=True,
        balance=Decimal("100.00")
    )
    db.add(invoice)
    
    payment_method = PaymentMethod(
        name="Check",
        requires_reference=True
    )
    db.add(payment_method)
    db.commit()
    
    adder = RetailInvoicePaymentAdder(db)
    
    with pytest.raises(ProcedureError, match="Payment reference required"):
        adder._validate_payment(invoice, Decimal("50.00"), "Check")
        
def test_create_payment_success(db: Session):
    """Test successful payment creation"""
    invoice = Invoice(
        is_retail=True,
        balance=Decimal("100.00"),
        customer_id=1
    )
    db.add(invoice)
    db.commit()
    
    adder = RetailInvoicePaymentAdder(db)
    payment = adder._create_payment(
        invoice,
        Decimal("50.00"),
        "Cash",
        notes="Test payment"
    )
    
    assert payment.invoice_id == invoice.id
    assert payment.customer_id == invoice.customer_id
    assert payment.amount == Decimal("50.00")
    assert payment.payment_method == "Cash"
    assert payment.notes == "Test payment"
    
def test_create_transaction_success(db: Session):
    """Test successful transaction creation"""
    invoice = Invoice(
        is_retail=True,
        balance=Decimal("100.00")
    )
    db.add(invoice)
    
    payment = Payment(
        invoice_id=invoice.id,
        amount=Decimal("50.00")
    )
    db.add(payment)
    db.commit()
    
    adder = RetailInvoicePaymentAdder(db)
    transaction = adder._create_transaction(
        invoice,
        payment,
        Decimal("50.00")
    )
    
    assert transaction.invoice_id == invoice.id
    assert transaction.payment_id == payment.id
    assert transaction.amount == Decimal("50.00")
    assert transaction.transaction_type == InvoiceTransactionType.PAYMENT
    
def test_update_invoice_balance_partial(db: Session):
    """Test invoice balance update with partial payment"""
    invoice = Invoice(
        is_retail=True,
        balance=Decimal("100.00"),
        status="Open"
    )
    db.add(invoice)
    db.commit()
    
    adder = RetailInvoicePaymentAdder(db)
    adder._update_invoice_balance(invoice, Decimal("50.00"))
    
    assert invoice.balance == Decimal("50.00")
    assert invoice.status == "Partial"
    assert invoice.last_payment_date is not None
    assert invoice.paid_date is None
    
def test_update_invoice_balance_full(db: Session):
    """Test invoice balance update with full payment"""
    invoice = Invoice(
        is_retail=True,
        balance=Decimal("100.00"),
        status="Open"
    )
    db.add(invoice)
    db.commit()
    
    adder = RetailInvoicePaymentAdder(db)
    adder._update_invoice_balance(invoice, Decimal("100.00"))
    
    assert invoice.balance == Decimal("0.00")
    assert invoice.status == "Paid"
    assert invoice.last_payment_date is not None
    assert invoice.paid_date is not None
    
def test_execute_full_process(db: Session):
    """Test full payment addition process"""
    # Setup test data
    invoice = Invoice(
        is_retail=True,
        balance=Decimal("100.00"),
        status="Open",
        customer_id=1
    )
    db.add(invoice)
    
    payment_method = PaymentMethod(
        name="Cash",
        requires_reference=False
    )
    db.add(payment_method)
    db.commit()
    
    # Execute payment addition
    RetailInvoicePaymentAdder.execute(
        db,
        invoice.id,
        Decimal("50.00"),
        "Cash",
        notes="Test payment"
    )
    
    # Verify results
    updated_invoice = db.query(Invoice).get(invoice.id)
    payment = db.query(Payment).filter_by(invoice_id=invoice.id).first()
    transaction = db.query(InvoiceTransaction).filter_by(invoice_id=invoice.id).first()
    
    assert updated_invoice.balance == Decimal("50.00")
    assert updated_invoice.status == "Partial"
    assert payment is not None
    assert payment.amount == Decimal("50.00")
    assert transaction is not None
    assert transaction.amount == Decimal("50.00")
