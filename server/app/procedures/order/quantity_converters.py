"""
Order Quantity Conversion Functions

Python implementation of functions for converting between ordered, delivered,
and billed quantities based on various time periods and converters.
"""
import math
from datetime import date, datetime
from decimal import Decimal
from typing import Union, Optional

from app.procedures.order.dos_utils import get_multiplier


def ordered_qty_to_billed_qty(
    from_date: Union[date, datetime],
    to_date: Union[date, datetime],
    ordered_qty: Union[float, Decimal],
    ordered_when: str,
    billed_when: str,
    ordered_converter: Union[float, Decimal],
    delivery_converter: Union[float, Decimal],
    billed_converter: Union[float, Decimal]
) -> float:
    """Convert ordered quantity to billed quantity.
    
    Args:
        from_date: Start date for the period
        to_date: End date for the period
        ordered_qty: Original ordered quantity
        ordered_when: Time period for ordering (e.g., 'MONTHLY', 'WEEKLY')
        billed_when: Time period for billing (e.g., 'MONTHLY', 'WEEKLY')
        ordered_converter: Conversion factor for ordered quantity
        delivery_converter: Conversion factor for delivery quantity
        billed_converter: Conversion factor for billed quantity
        
    Returns:
        float: Converted billed quantity
    
    Raises:
        ValueError: If any converter is less than or equal to zero
    """
    # Validate converters
    for name, value in [
        ('ordered_converter', ordered_converter),
        ('delivery_converter', delivery_converter),
        ('billed_converter', billed_converter)
    ]:
        if float(value) < 0.000000001:
            raise ValueError(f'Parameter {name} must be greater than zero')

    # Convert dates if needed
    if isinstance(from_date, datetime):
        from_date = from_date.date()
    if isinstance(to_date, datetime):
        to_date = to_date.date()

    # Get multiplier based on time periods
    multiplier = get_multiplier(
        from_date=from_date,
        to_date=to_date,
        from_when=ordered_when,
        to_when=billed_when
    )

    # Calculate converted quantity
    # 1. Convert ordered to delivery quantity
    delivery_qty = math.ceil(
        float(ordered_qty) * multiplier * float(ordered_converter) / float(delivery_converter)
    ) * float(delivery_converter)

    # 2. Convert delivery to billed quantity
    billed_qty = delivery_qty / float(billed_converter)

    return billed_qty


def ordered_qty_to_delivery_qty(
    from_date: Union[date, datetime],
    to_date: Union[date, datetime],
    ordered_qty: Union[float, Decimal],
    ordered_when: str,
    delivery_when: str,
    ordered_converter: Union[float, Decimal],
    delivery_converter: Union[float, Decimal]
) -> float:
    """Convert ordered quantity to delivery quantity.
    
    Args:
        from_date: Start date for the period
        to_date: End date for the period
        ordered_qty: Original ordered quantity
        ordered_when: Time period for ordering (e.g., 'MONTHLY', 'WEEKLY')
        delivery_when: Time period for delivery (e.g., 'MONTHLY', 'WEEKLY')
        ordered_converter: Conversion factor for ordered quantity
        delivery_converter: Conversion factor for delivery quantity
        
    Returns:
        float: Converted delivery quantity
    
    Raises:
        ValueError: If any converter is less than or equal to zero
    """
    # Validate converters
    for name, value in [
        ('ordered_converter', ordered_converter),
        ('delivery_converter', delivery_converter)
    ]:
        if float(value) < 0.000000001:
            raise ValueError(f'Parameter {name} must be greater than zero')

    # Convert dates if needed
    if isinstance(from_date, datetime):
        from_date = from_date.date()
    if isinstance(to_date, datetime):
        to_date = to_date.date()

    # Get multiplier based on time periods
    multiplier = get_multiplier(
        from_date=from_date,
        to_date=to_date,
        from_when=ordered_when,
        to_when=delivery_when
    )

    # Calculate converted quantity
    delivery_qty = math.ceil(
        float(ordered_qty) * multiplier * float(ordered_converter) / float(delivery_converter)
    ) * float(delivery_converter)

    return delivery_qty
