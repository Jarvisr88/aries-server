"""Test cases for the get_next_dos_to function."""

import pytest
from datetime import datetime
from app.procedures.scheduling.next_dos_to import get_next_dos_to

@pytest.fixture
def base_date():
    return datetime(2024, 1, 15)  # Mid-month date for testing

def test_invalid_dos_from():
    """Test that None is returned for invalid DOS From."""
    assert get_next_dos_to(
        dos_from=None,
        sale_rent_type='Sale',
        billing_month=1,
        billed_when='Monthly'
    ) is None

def test_sale_type(base_date):
    """Test that sales return same date for DOS To."""
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Sale',
        billing_month=1,
        billed_when='Monthly'
    )
    assert result == base_date

def test_end_date_reached(base_date):
    """Test that end date is respected when reached."""
    end_date = datetime(2024, 1, 10)  # Before base_date
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Rental',
        billing_month=1,
        billed_when='Monthly',
        end_date=end_date
    )
    assert result == end_date

def test_one_time_billing(base_date):
    """Test one-time billing returns same date."""
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Rental',
        billing_month=1,
        billed_when='One Time'
    )
    assert result == base_date

def test_monthly_first_month(base_date):
    """Test monthly billing for first month."""
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Rental',
        billing_month=1,
        billed_when='Monthly'
    )
    assert result == datetime(2024, 1, 31)

def test_monthly_second_month(base_date):
    """Test monthly billing for second month."""
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Rental',
        billing_month=2,
        billed_when='Monthly'
    )
    assert result == datetime(2024, 2, 29)  # February 2024 is a leap year

def test_monthly_year_transition(base_date):
    """Test monthly billing across year boundary."""
    dec_date = datetime(2024, 12, 15)
    result = get_next_dos_to(
        dos_from=dec_date,
        sale_rent_type='Rental',
        billing_month=2,
        billed_when='Monthly'
    )
    assert result == datetime(2025, 1, 31)

def test_weekly_billing(base_date):
    """Test weekly billing calculation."""
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Rental',
        billing_month=1,
        billed_when='Weekly'
    )
    assert result == datetime(2024, 1, 21)  # 6 days after start

def test_biweekly_billing(base_date):
    """Test bi-weekly billing calculation."""
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Rental',
        billing_month=1,
        billed_when='Bi-Weekly'
    )
    assert result == datetime(2024, 1, 28)  # 13 days after start

def test_custom_frequency(base_date):
    """Test custom frequency billing."""
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Rental',
        billing_month=1,
        billed_when='Custom',
        frequency='Every 3 Days',
        frequency_days=3
    )
    assert result == datetime(2024, 1, 17)  # 2 days after start (3 days inclusive)

def test_invalid_billing_frequency(base_date):
    """Test invalid billing frequency returns None."""
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Rental',
        billing_month=1,
        billed_when='Invalid'
    )
    assert result is None

def test_end_date_limit(base_date):
    """Test that DOS To doesn't exceed end date."""
    end_date = datetime(2024, 1, 20)
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Rental',
        billing_month=1,
        billed_when='Monthly',
        end_date=end_date
    )
    assert result == end_date

def test_capped_rental_monthly(base_date):
    """Test capped rental follows same rules as regular rental."""
    result = get_next_dos_to(
        dos_from=base_date,
        sale_rent_type='Capped Rental',
        billing_month=1,
        billed_when='Monthly'
    )
    assert result == datetime(2024, 1, 31)
