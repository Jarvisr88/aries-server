"""
Date of Service (DOS) Utility Functions

Helper functions for handling DOS calculations and quantity conversions.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Union


def get_multiplier(
    from_date: Union[date, datetime],
    to_date: Union[date, datetime],
    from_when: str,
    to_when: str
) -> float:
    """Get multiplier for converting between different time periods.
    
    Args:
        from_date: Start date for the period
        to_date: End date for the period
        from_when: Original time period (e.g., 'Daily', 'Weekly', 'Monthly')
        to_when: Target time period
        
    Returns:
        float: Multiplier for conversion between time periods
    """
    # Convert dates if needed
    if isinstance(from_date, datetime):
        from_date = from_date.date()
    if isinstance(to_date, datetime):
        to_date = to_date.date()

    # One Time orders always have multiplier of 1
    if from_when == 'One Time':
        return 1.0

    # Daily to various periods
    if from_when == 'Daily':
        if to_when == 'Daily':
            return 1.0
        elif to_when == 'Weekly':
            return 7.0
        elif to_when in ['Monthly', 'Calendar Monthly']:
            return (get_next_dos_from(from_date, to_date, to_when) - from_date).days
        elif to_when == 'Quarterly':
            return (get_next_dos_from(from_date, to_date, to_when) - from_date).days
        elif to_when == 'Semi-Annually':
            return (get_next_dos_from(from_date, to_date, to_when) - from_date).days
        elif to_when == 'Annually':
            return (get_next_dos_from(from_date, to_date, to_when) - from_date).days
        elif to_when == 'Custom':
            return (get_next_dos_from(from_date, to_date, to_when) - from_date).days

    # Weekly to various periods
    if from_when == 'Weekly':
        if to_when == 'Weekly':
            return 1.0
        elif to_when == 'Monthly':
            return 4.0
        elif to_when == 'Calendar Monthly':
            return (get_next_dos_from(from_date, to_date, to_when) - from_date).days / 7.0
        elif to_when == 'Quarterly':
            return 13.0
        elif to_when == 'Semi-Annually':
            return 26.0
        elif to_when == 'Annually':
            return 52.0

    # Monthly to various periods
    if from_when == 'Monthly':
        if to_when in ['Monthly', 'Calendar Monthly']:
            return 1.0
        elif to_when == 'Quarterly':
            return 3.0
        elif to_when == 'Semi-Annually':
            return 6.0
        elif to_when == 'Annually':
            return 12.0

    # Quarterly to various periods
    if from_when == 'Quarterly':
        if to_when == 'Quarterly':
            return 1.0
        elif to_when == 'Semi-Annually':
            return 2.0
        elif to_when == 'Annually':
            return 4.0

    # Semi-Annually to various periods
    if from_when == 'Semi-Annually':
        if to_when == 'Semi-Annually':
            return 1.0
        elif to_when == 'Annually':
            return 2.0

    # Annually to Annually
    if from_when == 'Annually' and to_when == 'Annually':
        return 1.0

    return 0.0  # Invalid combination


def get_new_dos_to(
    new_dos_from: date,
    old_dos_from: Optional[date],
    old_dos_to: Optional[date],
    actual_billed_when: Optional[date]
) -> Optional[date]:
    """Calculate new DOS To date based on date shifts.
    
    Args:
        new_dos_from: New DOS From date
        old_dos_from: Original DOS From date
        old_dos_to: Original DOS To date
        actual_billed_when: Actual billing date
        
    Returns:
        New DOS To date, or None if inputs are invalid
    """
    if not old_dos_from or not old_dos_to:
        return None

    # Calculate the original duration
    duration = (old_dos_to - old_dos_from).days

    # Apply the same duration to the new DOS From date
    new_dos_to = new_dos_from + timedelta(days=duration)

    # If there's an actual billing date, don't extend beyond it
    if actual_billed_when and new_dos_to > actual_billed_when:
        new_dos_to = actual_billed_when

    return new_dos_to


def ordered_qty_to_billed_qty(
    dos_from: date,
    dos_to: Optional[date],
    ordered_qty: Decimal,
    ordered_when: date,
    billed_when: Optional[date],
    ordered_converter: Optional[Decimal],
    delivery_converter: Optional[Decimal],
    billed_converter: Optional[Decimal]
) -> Decimal:
    """Convert ordered quantity to billed quantity based on dates and converters.
    
    Args:
        dos_from: DOS From date
        dos_to: DOS To date
        ordered_qty: Original ordered quantity
        ordered_when: Order date
        billed_when: Billing date
        ordered_converter: Converter for ordered quantity
        delivery_converter: Converter for delivery quantity
        billed_converter: Converter for billed quantity
        
    Returns:
        Converted billed quantity
    """
    if not dos_to or not ordered_qty:
        return Decimal('0')

    # Calculate duration in days
    duration = (dos_to - dos_from).days + 1

    # Apply converters if available
    qty = ordered_qty
    if ordered_converter and billed_converter:
        qty = (qty * ordered_converter) / billed_converter

    # Adjust for duration if billing date exists
    if billed_when:
        qty = qty * Decimal(duration)

    return qty


def ordered_qty_to_delivery_qty(
    dos_from: date,
    dos_to: Optional[date],
    ordered_qty: Decimal,
    ordered_when: date,
    billed_when: Optional[date],
    ordered_converter: Optional[Decimal],
    delivery_converter: Optional[Decimal],
    billed_converter: Optional[Decimal]
) -> Decimal:
    """Convert ordered quantity to delivery quantity based on dates and converters.
    
    Args:
        dos_from: DOS From date
        dos_to: DOS To date
        ordered_qty: Original ordered quantity
        ordered_when: Order date
        billed_when: Billing date
        ordered_converter: Converter for ordered quantity
        delivery_converter: Converter for delivery quantity
        billed_converter: Converter for billed quantity
        
    Returns:
        Converted delivery quantity
    """
    if not dos_to or not ordered_qty:
        return Decimal('0')

    # Apply converters if available
    qty = ordered_qty
    if ordered_converter and delivery_converter:
        qty = (qty * ordered_converter) / delivery_converter

    return qty
