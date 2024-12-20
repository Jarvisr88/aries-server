"""
Date Utility Functions for Billing

Helper functions for date calculations in billing procedures.
"""
from datetime import datetime, timedelta
from typing import Optional

from app.procedures.base import BaseProcedure


async def get_next_dos_from(
    from_date: datetime,
    to_date: datetime,
    billed_when: str
) -> datetime:
    """
    Calculate the next date of service based on billing frequency.
    
    Args:
        from_date: Start date
        to_date: End date
        billed_when: Billing frequency (Daily, Weekly, Monthly, etc.)
    
    Returns:
        datetime: Next date of service
    """
    if billed_when == 'Daily':
        return from_date + timedelta(days=1)
    elif billed_when == 'Weekly':
        return from_date + timedelta(days=7)
    elif billed_when == 'Monthly':
        # Add one month, handling edge cases
        year = from_date.year
        month = from_date.month + 1
        if month > 12:
            month = 1
            year += 1
        return datetime(year, month, from_date.day)
    elif billed_when == 'Quarterly':
        return from_date + timedelta(days=91)
    elif billed_when == 'Semi-Annually':
        return from_date + timedelta(days=182)
    elif billed_when == 'Annually':
        return from_date.replace(year=from_date.year + 1)
    else:
        return to_date  # Default to end date for unknown frequencies
