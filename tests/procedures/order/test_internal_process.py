"""Test cases for the OrderInternalProcess class."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session
from app.procedures.order.internal_process import OrderInternalProcess
from app.models.order import Order, OrderDetails
from app.models.invoice import Invoice, InvoiceDetails
from app.models.customer import CustomerInsurance
from app.models.inventory import InventoryItem
from app.models.pricing import PriceCode
from app.core.exceptions import ProcedureError

@pytest.fixture
def db():
    """Mock database session"""
    return Mock(spec=Session)

@pytest.fixture
def base_date():
    return datetime(2024, 1, 1)

@pytest.fixture
def order(base_date):
    """Sample order for testing"""
    return Order(
        id=1,
        customer_id=1,
        order_date=base_date,
        delivery_date=base_date,
        status='Open',
        total_amount=Decimal('100.00'),
        payment_amount=Decimal('0.00'),
        ordered_quantity=1,
        fulfilled_quantity=0,
        sale_rent_type='Sale'
    )

@pytest.fixture
def order_detail(order, base_date):
    """Sample order detail for testing"""
    return OrderDetails(
        customer_id=order.customer_id,
        order_id=order.id,
        inventory_item_id=1,
        dos_from=base_date,
        billing_month=1,
        billed_quantity=1,
        billable_price=Decimal('100.00'),
        is_active=True,
        actual_sale_rent_type='Sale',
        actual_billed_when='One Time',
        flat_rate=False
    )

def test_get_order_details(db, order, order_detail):
    """Test retrieving order details for processing"""
    db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [order_detail]
    
    processor = OrderInternalProcess(db)
    details = processor._get_order_details(order.id, 1, 0)
    
    assert len(details) == 1
    assert details[0] == order_detail

def test_create_invoice(db, order, base_date):
    """Test creating a new invoice"""
    processor = OrderInternalProcess(db)
    invoice = processor._create_invoice(order, base_date)
    
    assert invoice.customer_id == order.customer_id
    assert invoice.order_id == order.id
    assert invoice.date == base_date
    assert invoice.status == 'Open'

def test_create_invoice_detail(db, order, order_detail, base_date):
    """Test creating a new invoice detail"""
    invoice = Invoice(
        id=1,
        customer_id=order.customer_id,
        order_id=order.id,
        date=base_date
    )
    
    processor = OrderInternalProcess(db)
    detail = processor._create_invoice_detail(
        invoice=invoice,
        order_detail=order_detail,
        dos_from=base_date,
        dos_to=base_date,
        amount=Decimal('100.00')
    )
    
    assert detail.customer_id == invoice.customer_id
    assert detail.invoice_id == invoice.id
    assert detail.order_id == invoice.order_id
    assert detail.order_details_id == order_detail.id
    assert detail.amount == Decimal('100.00')

@patch('app.procedures.order.internal_process.order_must_be_skipped')
@patch('app.procedures.order.internal_process.get_next_dos_to')
@patch('app.procedures.order.internal_process.invoice_must_be_skipped')
@patch('app.procedures.order.internal_process.get_invoice_modifier')
@patch('app.procedures.order.internal_process.OrderDepositConverter.execute')
@patch('app.procedures.order.internal_process.order_must_be_closed')
def test_execute_full_process(
    mock_must_close,
    mock_convert_deposits,
    mock_get_modifier,
    mock_invoice_skip,
    mock_get_dos_to,
    mock_order_skip,
    db,
    order,
    order_detail,
    base_date
):
    """Test full order processing flow"""
    # Setup mocks
    db.query.return_value.get.return_value = order
    db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [order_detail]
    
    mock_order_skip.return_value = False
    mock_get_dos_to.return_value = base_date + timedelta(days=30)
    mock_invoice_skip.return_value = False
    mock_get_modifier.return_value = (Decimal('1.0'), 'No modification')
    mock_must_close.return_value = False
    
    # Execute procedure
    processor = OrderInternalProcess(db)
    invoice_id = processor._execute(
        order_id=order.id,
        billing_month=1,
        billing_flags=0,
        invoice_date=base_date
    )
    
    # Verify results
    assert invoice_id is not None
    assert db.add.call_count == 2  # Invoice and InvoiceDetails
    assert db.commit.call_count == 1
    mock_convert_deposits.assert_called_once_with(db, order.id)

def test_execute_no_order_details(db, order, base_date):
    """Test processing with no eligible order details"""
    db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = []
    
    processor = OrderInternalProcess(db)
    result = processor._execute(
        order_id=order.id,
        billing_month=1,
        billing_flags=0,
        invoice_date=base_date
    )
    
    assert result is None
    assert db.add.call_count == 0
    assert db.commit.call_count == 0

def test_execute_order_not_found(db, base_date):
    """Test processing with non-existent order"""
    db.query.return_value.get.return_value = None
    
    processor = OrderInternalProcess(db)
    with pytest.raises(ProcedureError):
        processor._execute(
            order_id=999,
            billing_month=1,
            billing_flags=0,
            invoice_date=base_date
        )

@patch('app.procedures.order.internal_process.order_must_be_skipped')
def test_execute_skip_order(mock_order_skip, db, order, order_detail, base_date):
    """Test processing when order should be skipped"""
    db.query.return_value.get.return_value = order
    db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [order_detail]
    mock_order_skip.return_value = True
    
    processor = OrderInternalProcess(db)
    invoice_id = processor._execute(
        order_id=order.id,
        billing_month=1,
        billing_flags=0,
        invoice_date=base_date
    )
    
    assert invoice_id is not None  # Invoice is created but empty
    assert db.add.call_count == 1  # Only Invoice, no InvoiceDetails
