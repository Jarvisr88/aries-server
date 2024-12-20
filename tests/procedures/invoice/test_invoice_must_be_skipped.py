"""Test cases for the invoice_must_be_skipped function."""

import pytest
from datetime import datetime, timedelta
from app.procedures.invoice.invoice_must_be_skipped import invoice_must_be_skipped

@pytest.fixture
def base_date():
    return datetime(2024, 1, 1)

def test_inactive_line_item(base_date):
    """Test that inactive line items are skipped."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=1,
        is_active=False
    ) is True

def test_completed_line_item(base_date):
    """Test that completed line items are skipped."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=1,
        is_completed=True
    ) is True

def test_fully_paid_line_item(base_date):
    """Test that fully paid line items are skipped."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=1,
        payment_amount=100.0,
        total_amount=100.0
    ) is True

def test_partially_paid_line_item(base_date):
    """Test that partially paid line items are not skipped."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=1,
        payment_amount=50.0,
        total_amount=100.0
    ) is False

def test_no_delivery_date(base_date):
    """Test that items with no delivery date are skipped."""
    assert invoice_must_be_skipped(
        delivery_date=None,
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=1
    ) is True

def test_sale_first_month(base_date):
    """Test that sales are not skipped in first month."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=1
    ) is False

def test_sale_subsequent_months(base_date):
    """Test that sales are skipped after first month."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=2
    ) is True

def test_rental_invalid_billing_month(base_date):
    """Test that rentals with invalid billing months are skipped."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=0
    ) is True

def test_rental_valid_billing_month(base_date):
    """Test that rentals with valid billing months are not skipped."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1
    ) is False

def test_dos_before_delivery(base_date):
    """Test that items with DOS before delivery are skipped."""
    assert invoice_must_be_skipped(
        delivery_date=base_date + timedelta(days=1),
        dos_from=base_date,
        actual_sale_rent_type='Sale',
        billing_month=1
    ) is True

def test_rental_replacement_modifier(base_date):
    """Test that rental replacements are skipped."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1,
        modifier1='RR'
    ) is True

def test_new_equipment_first_month(base_date):
    """Test that new equipment is not skipped in first month."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1,
        modifier1='NU'
    ) is False

def test_new_equipment_subsequent_months(base_date):
    """Test that new equipment is skipped after first month."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=2,
        modifier1='NU'
    ) is True

def test_kx_modifier_active(base_date):
    """Test that KX modifier with active status is not skipped."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1,
        modifier1='KX',
        is_active=True
    ) is False

def test_kx_modifier_inactive(base_date):
    """Test that KX modifier with inactive status is skipped."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1,
        modifier1='KX',
        is_active=False
    ) is True

def test_multiple_modifiers(base_date):
    """Test handling of multiple modifiers."""
    assert invoice_must_be_skipped(
        delivery_date=base_date,
        dos_from=base_date,
        actual_sale_rent_type='Rental',
        billing_month=1,
        modifier1='KX',
        modifier2='RR',
        is_active=True
    ) is True  # RR modifier takes precedence
