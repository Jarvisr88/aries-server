"""Test cases for the OrderInternalBalance class."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session
from app.procedures.order.internal_balance import OrderInternalBalance
from app.models.order import Order
from app.core.exceptions import ProcedureError

@pytest.fixture
def db():
    """Mock database session"""
    return Mock(spec=Session)

@pytest.fixture
def order():
    """Sample order for testing"""
    return Order(
        id=1,
        customer_id=1,
        status='Open',
        total_amount=Decimal('0.00'),
        payment_amount=Decimal('0.00'),
        balance_amount=Decimal('0.00'),
        ordered_quantity=0,
        fulfilled_quantity=0
    )

def test_get_invoice_totals(db):
    """Test retrieving invoice totals"""
    mock_result = Mock()
    mock_result.total_amount = Decimal('100.00')
    mock_result.total_paid = Decimal('50.00')
    db.query.return_value.join.return_value.outerjoin.return_value.filter.return_value.first.return_value = mock_result
    
    procedure = OrderInternalBalance(db)
    total_amount, total_paid = procedure._get_invoice_totals(1)
    
    assert total_amount == Decimal('100.00')
    assert total_paid == Decimal('50.00')

def test_get_invoice_totals_no_results(db):
    """Test retrieving invoice totals with no results"""
    mock_result = Mock()
    mock_result.total_amount = None
    mock_result.total_paid = None
    db.query.return_value.join.return_value.outerjoin.return_value.filter.return_value.first.return_value = mock_result
    
    procedure = OrderInternalBalance(db)
    total_amount, total_paid = procedure._get_invoice_totals(1)
    
    assert total_amount == Decimal('0.00')
    assert total_paid == Decimal('0.00')

def test_get_order_quantities(db):
    """Test retrieving order quantities"""
    mock_result = Mock()
    mock_result.ordered = 2
    mock_result.fulfilled = 1
    db.query.return_value.filter.return_value.first.return_value = mock_result
    
    procedure = OrderInternalBalance(db)
    ordered, fulfilled = procedure._get_order_quantities(1)
    
    assert ordered == 2
    assert fulfilled == 1

def test_get_order_quantities_no_results(db):
    """Test retrieving order quantities with no results"""
    mock_result = Mock()
    mock_result.ordered = None
    mock_result.fulfilled = None
    db.query.return_value.filter.return_value.first.return_value = mock_result
    
    procedure = OrderInternalBalance(db)
    ordered, fulfilled = procedure._get_order_quantities(1)
    
    assert ordered == 0
    assert fulfilled == 0

def test_execute_order_not_found(db):
    """Test updating balance for non-existent order"""
    db.query.return_value.get.return_value = None
    
    procedure = OrderInternalBalance(db)
    with pytest.raises(ProcedureError):
        procedure._execute(999)

def test_execute_update_balance_open(db, order):
    """Test updating balance for open order"""
    db.query.return_value.get.return_value = order
    
    mock_totals = Mock()
    mock_totals.total_amount = Decimal('100.00')
    mock_totals.total_paid = Decimal('0.00')
    db.query.return_value.join.return_value.outerjoin.return_value.filter.return_value.first.return_value = mock_totals
    
    mock_quantities = Mock()
    mock_quantities.ordered = 2
    mock_quantities.fulfilled = 0
    db.query.return_value.filter.return_value.first.return_value = mock_quantities
    
    procedure = OrderInternalBalance(db)
    procedure._execute(order.id)
    
    assert order.total_amount == Decimal('100.00')
    assert order.payment_amount == Decimal('0.00')
    assert order.balance_amount == Decimal('100.00')
    assert order.ordered_quantity == 2
    assert order.fulfilled_quantity == 0
    assert order.status == 'Open'

def test_execute_update_balance_partial(db, order):
    """Test updating balance for partially fulfilled order"""
    db.query.return_value.get.return_value = order
    
    mock_totals = Mock()
    mock_totals.total_amount = Decimal('100.00')
    mock_totals.total_paid = Decimal('50.00')
    db.query.return_value.join.return_value.outerjoin.return_value.filter.return_value.first.return_value = mock_totals
    
    mock_quantities = Mock()
    mock_quantities.ordered = 2
    mock_quantities.fulfilled = 1
    db.query.return_value.filter.return_value.first.return_value = mock_quantities
    
    procedure = OrderInternalBalance(db)
    procedure._execute(order.id)
    
    assert order.total_amount == Decimal('100.00')
    assert order.payment_amount == Decimal('50.00')
    assert order.balance_amount == Decimal('50.00')
    assert order.ordered_quantity == 2
    assert order.fulfilled_quantity == 1
    assert order.status == 'Partial'

def test_execute_update_balance_closed(db, order):
    """Test updating balance for closed order"""
    db.query.return_value.get.return_value = order
    
    mock_totals = Mock()
    mock_totals.total_amount = Decimal('100.00')
    mock_totals.total_paid = Decimal('100.00')
    db.query.return_value.join.return_value.outerjoin.return_value.filter.return_value.first.return_value = mock_totals
    
    mock_quantities = Mock()
    mock_quantities.ordered = 2
    mock_quantities.fulfilled = 2
    db.query.return_value.filter.return_value.first.return_value = mock_quantities
    
    procedure = OrderInternalBalance(db)
    procedure._execute(order.id)
    
    assert order.total_amount == Decimal('100.00')
    assert order.payment_amount == Decimal('100.00')
    assert order.balance_amount == Decimal('0.00')
    assert order.ordered_quantity == 2
    assert order.fulfilled_quantity == 2
    assert order.status == 'Closed'
