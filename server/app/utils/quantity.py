"""
Quantity Calculation Functions

Common quantity calculation functions used across the application.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


def ordered_qty_to_billed_qty(
    dos_from: date,
    dos_to: Optional[date],
    ordered_qty: Decimal,
    ordered_when: datetime,
    billed_when: Optional[datetime],
    ordered_converter: Optional[Decimal],
    delivery_converter: Optional[Decimal],
    billed_converter: Optional[Decimal]
) -> Decimal:
    """
    Convert ordered quantity to billed quantity based on dates and converters.
    
    Args:
        dos_from: Date of service start
        dos_to: Date of service end
        ordered_qty: Original ordered quantity
        ordered_when: When order was placed
        billed_when: When order was billed
        ordered_converter: Converter for ordered units
        delivery_converter: Converter for delivery units
        billed_converter: Converter for billed units
        
    Returns:
        Calculated billed quantity
    """
    if not dos_to or not ordered_qty:
        return Decimal('0')

    # Start with ordered quantity
    qty = ordered_qty

    # Apply converters if available
    if ordered_converter and billed_converter:
        qty = qty * (ordered_converter / billed_converter)

    # Adjust for billing period if needed
    if billed_when:
        days_total = (dos_to - dos_from).days + 1
        days_billed = (billed_when.date() - dos_from).days + 1
        
        if days_total > 0:
            qty = qty * (Decimal(days_billed) / Decimal(days_total))

    return qty.quantize(Decimal('.01'))


def ordered_qty_to_delivery_qty(
    dos_from: date,
    dos_to: Optional[date],
    ordered_qty: Decimal,
    ordered_when: datetime,
    billed_when: Optional[datetime],
    ordered_converter: Optional[Decimal],
    delivery_converter: Optional[Decimal],
    billed_converter: Optional[Decimal]
) -> Decimal:
    """
    Convert ordered quantity to delivery quantity based on dates and converters.
    
    Args:
        dos_from: Date of service start
        dos_to: Date of service end
        ordered_qty: Original ordered quantity
        ordered_when: When order was placed
        billed_when: When order was billed
        ordered_converter: Converter for ordered units
        delivery_converter: Converter for delivery units
        billed_converter: Converter for billed units
        
    Returns:
        Calculated delivery quantity
    """
    if not dos_to or not ordered_qty:
        return Decimal('0')

    # Start with ordered quantity
    qty = ordered_qty

    # Apply converters if available
    if ordered_converter and delivery_converter:
        qty = qty * (ordered_converter / delivery_converter)

    # No date adjustments for delivery quantity
    return qty.quantize(Decimal('.01'))
