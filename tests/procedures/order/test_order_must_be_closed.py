"""Test cases for the order_must_be_closed function."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app.procedures.order.order_must_be_closed import order_must_be_closed

@pytest.fixture
def base_date():
    return datetime(2024, 1, 1)

@pytest.fixture
def base_order_args(base_date):
    """Base arguments for a valid order."""
    return {
        'order_id': 1,
        'customer_id': 1,
        'order_date': base_date,
        'delivery_date': base_date,
        'end_date': None,
        'total_amount': Decimal('100.00'),
        'payment_amount': Decimal('0.00'),
        'ordered_quantity': 1,
        'fulfilled_quantity': 0,
        'sale_rent_type': 'Sale',
        'billing_month': 1,
        'is_active': True,
        'modifiers': None,
        'has_pending_claims': False,
        'has_pending_authorizations': False
    }

def test_inactive_order(base_order_args):
    """Test that inactive orders must be closed."""
    args = {**base_order_args, 'is_active': False}
    assert order_must_be_closed(**args) is True

def test_missing_required_data(base_order_args):
    """Test that orders with missing required data stay open."""
    args = {**base_order_args, 'order_id': None}
    assert order_must_be_closed(**args) is False

def test_sale_not_delivered(base_order_args):
    """Test that undelivered sales stay open."""
    args = {**base_order_args, 'delivery_date': None}
    assert order_must_be_closed(**args) is False

def test_sale_not_fully_paid(base_order_args):
    """Test that unpaid sales stay open."""
    args = {**base_order_args, 'payment_amount': Decimal('99.99')}
    assert order_must_be_closed(**args) is False

def test_sale_not_fulfilled(base_order_args):
    """Test that unfulfilled sales stay open."""
    args = {**base_order_args, 'fulfilled_quantity': 0}
    assert order_must_be_closed(**args) is False

def test_sale_with_pending_claims(base_order_args):
    """Test that sales with pending claims stay open."""
    args = {**base_order_args, 
           'payment_amount': Decimal('100.00'),
           'fulfilled_quantity': 1,
           'has_pending_claims': True}
    assert order_must_be_closed(**args) is False

def test_sale_with_pending_authorizations(base_order_args):
    """Test that sales with pending authorizations stay open."""
    args = {**base_order_args,
           'payment_amount': Decimal('100.00'),
           'fulfilled_quantity': 1,
           'has_pending_authorizations': True}
    assert order_must_be_closed(**args) is False

def test_completed_sale(base_order_args):
    """Test that completed sales are closed."""
    args = {**base_order_args,
           'payment_amount': Decimal('100.00'),
           'fulfilled_quantity': 1}
    assert order_must_be_closed(**args) is True

def test_rental_not_delivered(base_order_args):
    """Test that undelivered rentals stay open."""
    args = {**base_order_args,
           'sale_rent_type': 'Rental',
           'delivery_date': None}
    assert order_must_be_closed(**args) is False

def test_rental_end_date_not_reached(base_order_args, base_date):
    """Test that rentals before end date stay open."""
    args = {**base_order_args,
           'sale_rent_type': 'Rental',
           'end_date': base_date + timedelta(days=30)}
    assert order_must_be_closed(**args) is False

def test_rental_end_date_reached_not_paid(base_order_args, base_date):
    """Test that rentals after end date but not paid stay open."""
    args = {**base_order_args,
           'sale_rent_type': 'Rental',
           'end_date': base_date - timedelta(days=1)}
    assert order_must_be_closed(**args) is False

def test_rental_end_date_reached_and_paid(base_order_args, base_date):
    """Test that rentals after end date and paid are closed."""
    args = {**base_order_args,
           'sale_rent_type': 'Rental',
           'end_date': base_date - timedelta(days=1),
           'payment_amount': Decimal('100.00')}
    assert order_must_be_closed(**args) is True

def test_capped_rental_after_13_months(base_order_args):
    """Test that capped rentals after 13 months and paid are closed."""
    args = {**base_order_args,
           'sale_rent_type': 'Capped Rental',
           'billing_month': 14,
           'payment_amount': Decimal('100.00')}
    assert order_must_be_closed(**args) is True

def test_capped_rental_after_13_months_not_paid(base_order_args):
    """Test that capped rentals after 13 months but not paid stay open."""
    args = {**base_order_args,
           'sale_rent_type': 'Capped Rental',
           'billing_month': 14}
    assert order_must_be_closed(**args) is False

def test_rental_with_rr_modifier(base_order_args):
    """Test that rentals with RR modifier are closed."""
    args = {**base_order_args,
           'sale_rent_type': 'Rental',
           'modifiers': ['RR']}
    assert order_must_be_closed(**args) is True

def test_standard_rental(base_order_args):
    """Test that standard rentals stay open."""
    args = {**base_order_args, 'sale_rent_type': 'Rental'}
    assert order_must_be_closed(**args) is False
