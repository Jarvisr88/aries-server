"""
Billing Multiplier Function

Python implementation of the GetMultiplier function for
calculating billing multipliers based on order and billing frequencies.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from app.utils.date import get_next_dos_from


class BillingFrequency(str, Enum):
    """Billing frequency enumeration"""
    ONE_TIME = 'One Time'
    DAILY = 'Daily'
    WEEKLY = 'Weekly'
    MONTHLY = 'Monthly'
    CALENDAR_MONTHLY = 'Calendar Monthly'
    QUARTERLY = 'Quarterly'
    SEMI_ANNUALLY = 'Semi-Annually'
    ANNUALLY = 'Annually'


def get_multiplier(
    from_date: datetime,
    to_date: datetime,
    ordered_when: str,
    billed_when: str
) -> float:
    """
    Get billing multiplier based on order and billing frequencies.
    
    Args:
        from_date: Start date
        to_date: End date
        ordered_when: Order frequency
        billed_when: Billing frequency
        
    Returns:
        Billing multiplier
    """
    # One Time orders always have multiplier of 1
    if ordered_when == BillingFrequency.ONE_TIME:
        return 1.0

    # Daily billing frequencies
    if ordered_when == BillingFrequency.DAILY:
        if billed_when == BillingFrequency.DAILY:
            return 1.0
        elif billed_when == BillingFrequency.WEEKLY:
            return 7.0
        elif billed_when in [BillingFrequency.MONTHLY, BillingFrequency.CALENDAR_MONTHLY]:
            next_dos = get_next_dos_from(from_date, to_date, billed_when)
            return (next_dos - from_date).days
        elif billed_when == BillingFrequency.QUARTERLY:
            next_dos = get_next_dos_from(from_date, to_date, billed_when)
            return (next_dos - from_date).days
        elif billed_when == BillingFrequency.SEMI_ANNUALLY:
            next_dos = get_next_dos_from(from_date, to_date, billed_when)
            return (next_dos - from_date).days
        elif billed_when == BillingFrequency.ANNUALLY:
            next_dos = get_next_dos_from(from_date, to_date, billed_when)
            return (next_dos - from_date).days

    # Weekly billing frequencies
    elif ordered_when == BillingFrequency.WEEKLY:
        if billed_when == BillingFrequency.WEEKLY:
            return 1.0
        elif billed_when == BillingFrequency.MONTHLY:
            return 4.0
        elif billed_when == BillingFrequency.CALENDAR_MONTHLY:
            next_dos = get_next_dos_from(from_date, to_date, billed_when)
            return (next_dos - from_date).days / 7.0
        elif billed_when == BillingFrequency.QUARTERLY:
            return 13.0
        elif billed_when == BillingFrequency.SEMI_ANNUALLY:
            return 26.0
        elif billed_when == BillingFrequency.ANNUALLY:
            return 52.0

    # Monthly billing frequencies
    elif ordered_when == BillingFrequency.MONTHLY:
        if billed_when == BillingFrequency.MONTHLY:
            return 1.0
        elif billed_when == BillingFrequency.CALENDAR_MONTHLY:
            return 1.0
        elif billed_when == BillingFrequency.QUARTERLY:
            return 3.0
        elif billed_when == BillingFrequency.SEMI_ANNUALLY:
            return 6.0
        elif billed_when == BillingFrequency.ANNUALLY:
            return 12.0

    # Quarterly billing frequencies
    elif ordered_when == BillingFrequency.QUARTERLY:
        if billed_when == BillingFrequency.QUARTERLY:
            return 1.0
        elif billed_when == BillingFrequency.SEMI_ANNUALLY:
            return 2.0
        elif billed_when == BillingFrequency.ANNUALLY:
            return 4.0

    # Semi-Annual billing frequencies
    elif ordered_when == BillingFrequency.SEMI_ANNUALLY:
        if billed_when == BillingFrequency.SEMI_ANNUALLY:
            return 1.0
        elif billed_when == BillingFrequency.ANNUALLY:
            return 2.0

    # Annual billing frequencies
    elif ordered_when == BillingFrequency.ANNUALLY:
        if billed_when == BillingFrequency.ANNUALLY:
            return 1.0

    # Default case
    return 1.0
