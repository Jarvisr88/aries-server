"""Tests for invoice transaction trigger functionality"""
import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.invoice import (
    InvoiceTransaction,
    InvoiceTransactionType,
    InvoiceDetails
)
from app.triggers.invoice_transaction import InvoiceTransactionTrigger


@pytest.fixture
def db_session():
    """Provide a database session"""
    # Setup test database session
    pass


@pytest.fixture
def trigger(db_session):
    """Provide an invoice transaction trigger instance"""
    return InvoiceTransactionTrigger(db_session)


@pytest.fixture
async def invoice_details(db_session):
    """Create test invoice details"""
    detail = InvoiceDetails(
        customer_id=1,
        invoice_id=1,
        id=1,
        quantity=2.0,
        allowable_amount=Decimal('100.00'),
        billable_amount=Decimal('120.00'),
        taxes=Decimal('10.00')
    )
    db_session.add(detail)
    await db_session.commit()
    return detail


@pytest.fixture
async def transaction_type(db_session):
    """Create test transaction type"""
    type_adjust = InvoiceTransactionType(
        id=1,
        name='Adjust Allowable'
    )
    db_session.add(type_adjust)
    await db_session.commit()
    return type_adjust


async def test_adjust_allowable(
    db_session,
    trigger,
    invoice_details,
    transaction_type
):
    """Test adjusting allowable amount"""
    # Create test transaction
    transaction = InvoiceTransaction(
        customer_id=1,
        invoice_id=1,
        invoice_details_id=1,
        transaction_type_id=1,
        amount=Decimal('150.00'),
        transaction_date=datetime.now()
    )

    # Execute trigger
    await trigger.before_insert(transaction)

    # Verify results
    assert transaction.quantity == 2.0
    assert transaction.comments == 'Previous Value=100.00'
    
    # Check invoice details update
    detail = await db_session.get(InvoiceDetails, 1)
    assert detail.allowable_amount == Decimal('150.00')


async def test_no_update_small_difference(
    db_session,
    trigger,
    invoice_details,
    transaction_type
):
    """Test no update when difference is small"""
    # Create test transaction with small difference
    transaction = InvoiceTransaction(
        customer_id=1,
        invoice_id=1,
        invoice_details_id=1,
        transaction_type_id=1,
        amount=Decimal('100.0001'),
        transaction_date=datetime.now()
    )

    # Execute trigger
    await trigger.before_insert(transaction)

    # Verify no update
    detail = await db_session.get(InvoiceDetails, 1)
    assert detail.allowable_amount == Decimal('100.00')


async def test_invalid_transaction_type(
    db_session,
    trigger,
    invoice_details
):
    """Test handling of invalid transaction type"""
    # Create test transaction with invalid type
    transaction = InvoiceTransaction(
        customer_id=1,
        invoice_id=1,
        invoice_details_id=1,
        transaction_type_id=999,
        amount=Decimal('150.00'),
        transaction_date=datetime.now()
    )

    # Execute trigger
    await trigger.before_insert(transaction)

    # Verify no changes
    detail = await db_session.get(InvoiceDetails, 1)
    assert detail.allowable_amount == Decimal('100.00')
    assert not transaction.comments
