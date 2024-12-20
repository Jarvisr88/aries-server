"""Test cases for the order_must_be_skipped function."""

import pytest
from datetime import datetime, timedelta
from app.procedures.order.order_must_be_skipped import order_must_be_skipped

@pytest.fixture
def base_date():
    return datetime(2024, 1, 1)

def test_no_delivery_date(base_date):
    """Test that orders with no delivery date are skipped."""
    assert order_must_be_skipped(
        delivery_date=None,
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=1
    ) is True

def test_sale_first_month(base_date):
    """Test that sales are not skipped in the first month."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=1
    ) is False

def test_sale_subsequent_months(base_date):
    """Test that sales are skipped after the first month."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=2
    ) is True

def test_rental_invalid_billing_month(base_date):
    """Test that rentals with invalid billing months are skipped."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=0
    ) is True

def test_rental_valid_billing_month(base_date):
    """Test that rentals with valid billing months are not skipped."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1
    ) is False

def test_dos_before_delivery(base_date):
    """Test that orders with DOS before delivery date are skipped."""
    assert order_must_be_skipped(
        delivery_date=base_date + timedelta(days=1),
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=1
    ) is True

def test_rental_replacement_modifier(base_date):
    """Test that rental replacement orders are skipped."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1,
        modifier1='RR'
    ) is True

def test_new_equipment_first_month(base_date):
    """Test that new equipment is not skipped in first month."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1,
        modifier1='NU'
    ) is False

def test_new_equipment_subsequent_months(base_date):
    """Test that new equipment is skipped after first month."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=2,
        modifier1='NU'
    ) is True

def test_used_equipment_first_month(base_date):
    """Test that used equipment is not skipped in first month."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1,
        modifier1='UE'
    ) is False

def test_used_equipment_subsequent_months(base_date):
    """Test that used equipment is skipped after first month."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=2,
        modifier1='UE'
    ) is True

def test_multiple_modifiers(base_date):
    """Test handling of multiple modifiers."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1,
        modifier1='NU',
        modifier2='RR'
    ) is True  # RR modifier takes precedence

def test_capped_rental(base_date):
    """Test that capped rentals follow rental rules."""
    assert order_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Capped Rental',
        billing_month=1
    ) is False
