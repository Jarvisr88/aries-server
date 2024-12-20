"""Test cases for the get_invoice_modifier function."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app.procedures.invoice.invoice_modifier import get_invoice_modifier

@pytest.fixture
def base_date():
    return datetime(2024, 1, 1)

def test_sale_type(base_date):
    """Test that sales have no modifier."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Sale',
        billing_month=1,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30)
    )
    assert modifier == Decimal('1.0')
    assert reason == 'Standard sale pricing'

def test_repair_item(base_date):
    """Test that repairs have zero charge."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Rental',
        billing_month=1,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30),
        is_repair=True
    )
    assert modifier == Decimal('0.0')
    assert reason == 'No charge for repair'

def test_replacement_item(base_date):
    """Test that replacements have zero charge."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Rental',
        billing_month=1,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30),
        is_replacement=True
    )
    assert modifier == Decimal('0.0')
    assert reason == 'No charge for replacement'

def test_rental_replacement_modifier(base_date):
    """Test that rental replacements have zero charge."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Rental',
        billing_month=1,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30),
        modifier1='RR'
    )
    assert modifier == Decimal('0.0')
    assert reason == 'No charge for rental replacement'

def test_capped_rental_over_13_months(base_date):
    """Test that capped rentals are free after 13 months."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Capped Rental',
        billing_month=14,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30)
    )
    assert modifier == Decimal('0.0')
    assert reason == 'Capped rental exceeded 13 months'

def test_capped_rental_11_to_13_months(base_date):
    """Test that capped rentals have reduced rate for months 11-13."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Capped Rental',
        billing_month=11,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30)
    )
    assert modifier == Decimal('0.75')
    assert reason == 'Capped rental months 11-13'

def test_new_equipment_first_month(base_date):
    """Test new equipment pricing for first month."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Rental',
        billing_month=1,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30),
        modifier1='NU'
    )
    assert modifier == Decimal('1.0')
    assert reason == 'New equipment first month'

def test_new_equipment_months_2_3(base_date):
    """Test new equipment pricing for months 2-3."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Rental',
        billing_month=2,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30),
        modifier1='NU'
    )
    assert modifier == Decimal('0.75')
    assert reason == 'New equipment months 2-3'

def test_new_equipment_after_month_3(base_date):
    """Test new equipment pricing after month 3."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Rental',
        billing_month=4,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30),
        modifier1='NU'
    )
    assert modifier == Decimal('0.5')
    assert reason == 'New equipment after month 3'

def test_used_equipment_first_month(base_date):
    """Test used equipment pricing for first month."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Rental',
        billing_month=1,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30),
        modifier1='UE'
    )
    assert modifier == Decimal('0.75')
    assert reason == 'Used equipment first month'

def test_used_equipment_after_first_month(base_date):
    """Test used equipment pricing after first month."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Rental',
        billing_month=2,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30),
        modifier1='UE'
    )
    assert modifier == Decimal('0.5')
    assert reason == 'Used equipment after month 1'

def test_partial_month(base_date):
    """Test partial month calculation."""
    end_date = base_date + timedelta(days=15)  # Half month
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Rental',
        billing_month=1,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30),
        end_date=end_date
    )
    assert modifier == Decimal('0.5')  # 16/31 days ≈ 0.5
    assert reason == 'Partial month: 16/31 days'

def test_standard_rental(base_date):
    """Test standard rental with no special conditions."""
    modifier, reason = get_invoice_modifier(
        sale_rent_type='Rental',
        billing_month=1,
        dos_from=base_date,
        dos_to=base_date + timedelta(days=30)
    )
    assert modifier == Decimal('1.0')
    assert reason == 'Standard rental pricing'
