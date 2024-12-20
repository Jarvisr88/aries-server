"""
Module for handling Date of Service (DOS) calculations.

This module provides functionality for calculating the next DOS date based on
various frequency patterns commonly used in medical billing and scheduling.
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional


def get_next_dos_from(from_date: datetime, to_date: Optional[datetime], frequency: str) -> datetime:
    """
    Calculate the next Date of Service (DOS) based on a frequency pattern.

    Args:
        from_date (datetime): The starting date to calculate from
        to_date (datetime, optional): The end date (not used in current implementation but kept for API compatibility)
        frequency (str): The frequency pattern for calculating next DOS.
            Valid values are:
            - 'One time'
            - 'Daily'
            - 'Weekly'
            - 'Monthly'
            - 'Calendar Monthly'
            - 'Quarterly'
            - 'Semi-Annually'
            - 'Annually'

    Returns:
        datetime: The calculated next DOS date

    Raises:
        ValueError: If an invalid frequency is provided
    """
    frequency = frequency.strip()
    
    # Direct return for one-time frequency
    if frequency == 'One time':
        return from_date

    # Simple interval calculations
    interval_map = {
        'Daily': relativedelta(days=1),
        'Weekly': relativedelta(days=7),
        'Monthly': relativedelta(months=1),
        'Quarterly': relativedelta(months=3),
        'Semi-Annually': relativedelta(months=6),
        'Annually': relativedelta(months=12)
    }

    if frequency in interval_map:
        return from_date + interval_map[frequency]

    # Special handling for Calendar Monthly
    if frequency == 'Calendar Monthly':
        # Add one month and set to first of month
        next_date = from_date + relativedelta(months=1)
        return next_date.replace(day=1)

    raise ValueError(f"Invalid frequency pattern: {frequency}")


def validate_frequency(frequency: str) -> bool:
    """
    Validate if a given frequency pattern is supported.

    Args:
        frequency (str): The frequency pattern to validate

    Returns:
        bool: True if the frequency is valid, False otherwise
    """
    valid_frequencies = {
        'One time',
        'Daily',
        'Weekly',
        'Monthly',
        'Calendar Monthly',
        'Quarterly',
        'Semi-Annually',
        'Annually'
    }
    return frequency.strip() in valid_frequencies
