"""
Date Utility Functions

Common date manipulation functions used across the application.
"""
from datetime import date, datetime, timedelta
from typing import Optional


def get_new_dos_to(
    new_dos_from: date,
    old_dos_from: Optional[date],
    old_dos_to: Optional[date],
    actual_billed_when: Optional[datetime]
) -> Optional[date]:
    """
    Calculate new DOS To date based on changes to DOS From.
    
    Args:
        new_dos_from: New DOS From date
        old_dos_from: Original DOS From date
        old_dos_to: Original DOS To date
        actual_billed_when: Actual billing datetime
        
    Returns:
        New DOS To date or None if inputs invalid
    """
    if not new_dos_from or not old_dos_from or not old_dos_to:
        return None

    # Calculate date difference
    days_diff = (old_dos_to - old_dos_from).days
    
    # Apply same difference to new DOS From
    new_dos_to = new_dos_from + timedelta(days=days_diff)
    
    # If actual billed date exists, don't extend beyond it
    if actual_billed_when:
        actual_billed_date = actual_billed_when.date()
        if new_dos_to > actual_billed_date:
            new_dos_to = actual_billed_date
            
    return new_dos_to


def get_next_dos_from(
    from_date: datetime,
    to_date: datetime,
    billing_frequency: str
) -> datetime:
    """
    Calculate next DOS From date based on billing frequency.
    
    Args:
        from_date: Current DOS From date
        to_date: Current DOS To date
        billing_frequency: Billing frequency (e.g., 'Monthly', 'Quarterly')
        
    Returns:
        Next DOS From date
    """
    if billing_frequency == 'Monthly':
        # Add one month
        if from_date.month == 12:
            return datetime(from_date.year + 1, 1, from_date.day)
        else:
            return datetime(from_date.year, from_date.month + 1, from_date.day)

    elif billing_frequency == 'Calendar Monthly':
        # First day of next month
        if from_date.month == 12:
            return datetime(from_date.year + 1, 1, 1)
        else:
            return datetime(from_date.year, from_date.month + 1, 1)

    elif billing_frequency == 'Quarterly':
        # Add three months
        year = from_date.year
        month = from_date.month + 3
        if month > 12:
            year += month // 12
            month = month % 12 or 12
        return datetime(year, month, from_date.day)

    elif billing_frequency == 'Semi-Annually':
        # Add six months
        year = from_date.year
        month = from_date.month + 6
        if month > 12:
            year += month // 12
            month = month % 12 or 12
        return datetime(year, month, from_date.day)

    elif billing_frequency == 'Annually':
        # Add one year
        return datetime(from_date.year + 1, from_date.month, from_date.day)

    # Default to next day for other frequencies
    return from_date + timedelta(days=1)
