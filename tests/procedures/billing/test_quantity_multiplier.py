"""
Tests for the quantity_multiplier module.
"""

import pytest
from datetime import datetime, timedelta
from app.procedures.billing.quantity_multiplier import (
    get_quantity_multiplier,
    validate_sale_rent_type
)


@pytest.mark.parametrize("sale_rent_type", [
    'One Time Sale',
    'Re-occurring Sale',
    'Rent to Purchase',
    'Capped Rental',
    'Parental Capped Rental',
    'Medicare Oxygen Rental'
])
def test_unit_multiplier_types(sale_rent_type):
    """Test sale types that should always return 1."""
    from_date = datetime(2024, 1, 1)
    to_date = datetime(2024, 1, 31)
    result = get_quantity_multiplier(
        from_date=from_date,
        to_date=to_date,
        pickup_date=None,
        sale_rent_type=sale_rent_type,
        ordered_when='Daily',
        billed_when='Monthly'
    )
    assert result == 1.0


def test_monthly_rental_daily_order():
    """Test monthly rental with daily ordering."""
    from_date = datetime(2024, 1, 1)
    to_date = datetime(2024, 1, 31)
    pickup_date = datetime(2024, 1, 15)

    # Test with no pickup date
    result = get_quantity_multiplier(
        from_date=from_date,
        to_date=to_date,
        pickup_date=None,
        sale_rent_type='Monthly Rental',
        ordered_when='Daily',
        billed_when='Monthly'
    )
    assert result == 31  # Full month

    # Test with pickup date after next_to_date
    result = get_quantity_multiplier(
        from_date=from_date,
        to_date=to_date,
        pickup_date=datetime(2024, 2, 1),
        sale_rent_type='Monthly Rental',
        ordered_when='Daily',
        billed_when='Monthly'
    )
    assert result == 31  # Full month

    # Test with pickup date during period
    result = get_quantity_multiplier(
        from_date=from_date,
        to_date=to_date,
        pickup_date=pickup_date,
        sale_rent_type='Monthly Rental',
        ordered_when='Daily',
        billed_when='Monthly'
    )
    assert result == 15  # Days until pickup + 1

    # Test with pickup date before from_date
    result = get_quantity_multiplier(
        from_date=datetime(2024, 1, 16),
        to_date=to_date,
        pickup_date=pickup_date,
        sale_rent_type='Monthly Rental',
        ordered_when='Daily',
        billed_when='Monthly'
    )
    assert result == 0  # No days counted


def test_monthly_rental_non_daily_order():
    """Test monthly rental with non-daily ordering."""
    result = get_quantity_multiplier(
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 1, 31),
        pickup_date=None,
        sale_rent_type='Monthly Rental',
        ordered_when='Monthly',
        billed_when='Monthly'
    )
    assert result == 1.0


def test_one_time_rental():
    """Test one time rental calculations."""
    from_date = datetime(2024, 1, 1)
    pickup_date = datetime(2024, 1, 15)
    
    result = get_quantity_multiplier(
        from_date=from_date,
        to_date=datetime(2024, 1, 31),
        pickup_date=pickup_date,
        sale_rent_type='One Time Rental',
        ordered_when='Daily',
        billed_when='Monthly'
    )
    assert result == 15  # Days between from_date and pickup_date + 1

    # Test without pickup date
    with pytest.raises(ValueError) as exc_info:
        get_quantity_multiplier(
            from_date=from_date,
            to_date=datetime(2024, 1, 31),
            pickup_date=None,
            sale_rent_type='One Time Rental',
            ordered_when='Daily',
            billed_when='Monthly'
        )
    assert "Pickup date is required" in str(exc_info.value)


def test_invalid_sale_rent_type():
    """Test handling of invalid sale/rent type."""
    with pytest.raises(ValueError) as exc_info:
        get_quantity_multiplier(
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 31),
            pickup_date=None,
            sale_rent_type='Invalid Type',
            ordered_when='Daily',
            billed_when='Monthly'
        )
    assert "Invalid sale/rent type" in str(exc_info.value)


@pytest.mark.parametrize("sale_rent_type,expected", [
    ('One Time Sale', True),
    ('Re-occurring Sale', True),
    ('Rent to Purchase', True),
    ('Capped Rental', True),
    ('Parental Capped Rental', True),
    ('Medicare Oxygen Rental', True),
    ('Monthly Rental', True),
    ('One Time Rental', True),
    ('Invalid', False),
    ('', False),
    ('  Monthly Rental  ', True),  # Test with whitespace
])
def test_validate_sale_rent_type(sale_rent_type, expected):
    """Test sale/rent type validation."""
    assert validate_sale_rent_type(sale_rent_type) == expected
