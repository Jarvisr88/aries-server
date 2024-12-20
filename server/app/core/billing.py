"""
Core billing calculation functions for the Aries Enterprise system.

These functions handle various billing calculations including:
- Amount multipliers based on billing frequency and type
- Insurance allowable amounts
- Billable amounts for different sale/rental types
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal

def get_amount_multiplier(
    dos_from: date,
    dos_to: Optional[date],
    end_date: Optional[date],
    sale_rent_type: str,
    ordered_when: str,
    billed_when: str
) -> Decimal:
    """
    Calculate the amount multiplier based on billing parameters
    
    Args:
        dos_from: Start date of service
        dos_to: End date of service
        end_date: Final end date (if any)
        sale_rent_type: Type of sale/rental
        ordered_when: When the item was ordered
        billed_when: When the item should be billed
        
    Returns:
        Decimal multiplier to apply to base amount
    """
    # One-time sales always have multiplier of 1
    if sale_rent_type == 'Sale' and billed_when == 'One Time':
        return Decimal('1.00')
        
    # For rentals, calculate based on billing frequency
    if sale_rent_type == 'Rental':
        # If no DOS end date, use 1
        if not dos_to:
            return Decimal('1.00')
            
        # Calculate days in period
        days = (dos_to - dos_from).days + 1
        
        # Apply frequency multiplier
        if billed_when == 'Daily':
            return Decimal(str(days))
        elif billed_when == 'Weekly':
            return Decimal(str(days / 7)).quantize(Decimal('0.01'))
        elif billed_when == 'Monthly':
            return Decimal(str(days / 30)).quantize(Decimal('0.01'))
        elif billed_when == 'Quarterly':
            return Decimal(str(days / 90)).quantize(Decimal('0.01'))
        elif billed_when == 'Annually':
            return Decimal(str(days / 365)).quantize(Decimal('0.01'))
            
    # Re-occurring sales use unit multiplier
    return Decimal('1.00')

def get_quantity_multiplier(
    sale_rent_type: str,
    ordered_when: str,
    billed_when: str,
    frequency: Optional[str] = None,
    units_per_freq: Optional[int] = None
) -> Decimal:
    """
    Calculate the quantity multiplier based on billing parameters
    
    Args:
        sale_rent_type: Type of sale/rental ('Sale' or 'Rental')
        ordered_when: When the item was ordered ('One Time' or 'Recurring')
        billed_when: When the item should be billed ('One Time', 'Daily', 'Weekly', etc.)
        frequency: Optional frequency for recurring orders ('Daily', 'Weekly', etc.)
        units_per_freq: Optional units per frequency period
        
    Returns:
        Decimal multiplier to apply to base quantity
    """
    # One-time sales/orders always have multiplier of 1
    if ordered_when == 'One Time' or billed_when == 'One Time':
        return Decimal('1.00')
        
    # For recurring orders, calculate based on frequency
    if ordered_when == 'Recurring':
        if not frequency or not units_per_freq:
            return Decimal('1.00')
            
        # Convert frequencies to days
        freq_days = {
            'Daily': 1,
            'Weekly': 7,
            'Monthly': 30,
            'Quarterly': 90,
            'Annually': 365
        }
        
        # Calculate daily units
        daily_units = (units_per_freq / freq_days[frequency])
        
        # Convert to billing frequency
        if billed_when == 'Daily':
            return Decimal(str(daily_units)).quantize(Decimal('0.01'))
        elif billed_when == 'Weekly':
            return Decimal(str(daily_units * 7)).quantize(Decimal('0.01'))
        elif billed_when == 'Monthly':
            return Decimal(str(daily_units * 30)).quantize(Decimal('0.01'))
        elif billed_when == 'Quarterly':
            return Decimal(str(daily_units * 90)).quantize(Decimal('0.01'))
        elif billed_when == 'Annually':
            return Decimal(str(daily_units * 365)).quantize(Decimal('0.01'))
            
    return Decimal('1.00')

def get_allowable_amount(
    sale_rent_type: str,
    billing_month: int,
    allowable_price: Optional[Decimal],
    billed_quantity: Decimal,
    sale_allowable_price: Optional[Decimal],
    flat_rate: bool
) -> Decimal:
    """
    Calculate the insurance allowable amount
    
    Args:
        sale_rent_type: Type of sale/rental
        billing_month: Billing month number
        allowable_price: Base allowable price
        billed_quantity: Quantity being billed
        sale_allowable_price: Allowable price for sales
        flat_rate: Whether this is a flat rate item
        
    Returns:
        Calculated allowable amount
    """
    # Use sale price for first month of rentals or sales
    if billing_month <= 1 or sale_rent_type == 'Sale':
        base_price = sale_allowable_price or allowable_price or Decimal('0.00')
    else:
        base_price = allowable_price or Decimal('0.00')
        
    # For flat rate items, quantity is always 1
    if flat_rate:
        return base_price
        
    return (base_price * billed_quantity).quantize(Decimal('0.01'))

def get_billable_amount(
    sale_rent_type: str,
    billing_month: int,
    billable_price: Optional[Decimal],
    billed_quantity: Decimal,
    sale_billable_price: Optional[Decimal],
    flat_rate: bool
) -> Decimal:
    """
    Calculate the billable amount
    
    Args:
        sale_rent_type: Type of sale/rental
        billing_month: Billing month number
        billable_price: Base billable price
        billed_quantity: Quantity being billed
        sale_billable_price: Billable price for sales
        flat_rate: Whether this is a flat rate item
        
    Returns:
        Calculated billable amount
    """
    # Use sale price for first month of rentals or sales
    if billing_month <= 1 or sale_rent_type == 'Sale':
        base_price = sale_billable_price or billable_price or Decimal('0.00')
    else:
        base_price = billable_price or Decimal('0.00')
        
    # For flat rate items, quantity is always 1
    if flat_rate:
        return base_price
        
    return (base_price * billed_quantity).quantize(Decimal('0.01'))
