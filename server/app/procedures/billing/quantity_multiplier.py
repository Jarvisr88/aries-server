"""
Module for calculating quantity multipliers used in billing calculations.

This module provides functionality for determining the quantity multiplier
based on sale/rental type and various date parameters.
"""

from datetime import datetime
from typing import Optional
from app.procedures.scheduling.next_dos import get_next_dos_from


def get_quantity_multiplier(
    from_date: datetime,
    to_date: datetime,
    pickup_date: Optional[datetime],
    sale_rent_type: str,
    ordered_when: str,
    billed_when: str
) -> float:
    """
    Calculate the quantity multiplier for billing based on various parameters.

    Args:
        from_date (datetime): The start date for the calculation
        to_date (datetime): The end date for the calculation
        pickup_date (datetime, optional): The pickup date, if applicable
        sale_rent_type (str): The type of sale or rental
            Valid values include:
            - 'One Time Sale'
            - 'Re-occurring Sale'
            - 'Rent to Purchase'
            - 'Capped Rental'
            - 'Parental Capped Rental'
            - 'Medicare Oxygen Rental'
            - 'Monthly Rental'
            - 'One Time Rental'
        ordered_when (str): The ordering frequency (e.g., 'Daily')
        billed_when (str): The billing frequency

    Returns:
        float: The calculated quantity multiplier

    Raises:
        ValueError: If an invalid sale_rent_type is provided
    """
    # List of sale types that always return 1
    unit_multiplier_types = {
        'One Time Sale',
        'Re-occurring Sale',
        'Rent to Purchase',
        'Capped Rental',
        'Parental Capped Rental',
        'Medicare Oxygen Rental'
    }

    if sale_rent_type in unit_multiplier_types:
        return 1.0

    if sale_rent_type == 'Monthly Rental':
        if ordered_when == 'Daily':
            next_to_date = get_next_dos_from(from_date, to_date, billed_when)
            
            if pickup_date is None:
                return (next_to_date - from_date).days
            
            if next_to_date <= pickup_date:
                return (next_to_date - from_date).days
            
            if from_date <= pickup_date:
                return (pickup_date - from_date).days + 1
            
            # pickup_date < from_date
            return 0
        else:
            return 1.0

    if sale_rent_type == 'One Time Rental':
        if pickup_date is None:
            raise ValueError("Pickup date is required for One Time Rental")
        return (pickup_date - from_date).days + 1

    raise ValueError(f"Invalid sale/rent type: {sale_rent_type}")


def validate_sale_rent_type(sale_rent_type: str) -> bool:
    """
    Validate if a given sale/rent type is supported.

    Args:
        sale_rent_type (str): The sale/rent type to validate

    Returns:
        bool: True if the sale/rent type is valid, False otherwise
    """
    valid_types = {
        'One Time Sale',
        'Re-occurring Sale',
        'Rent to Purchase',
        'Capped Rental',
        'Parental Capped Rental',
        'Medicare Oxygen Rental',
        'Monthly Rental',
        'One Time Rental'
    }
    return sale_rent_type.strip() in valid_types
