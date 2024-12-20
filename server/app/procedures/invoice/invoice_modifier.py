"""
Function to determine the appropriate invoice modifier based on billing parameters.

This function calculates the invoice modifier to be applied based on rental type,
billing month, and other parameters that affect pricing.
"""
from datetime import datetime
from typing import Optional, Tuple
from decimal import Decimal

def get_invoice_modifier(
    sale_rent_type: str,
    billing_month: int,
    dos_from: datetime,
    dos_to: datetime,
    end_date: Optional[datetime] = None,
    modifier1: Optional[str] = None,
    modifier2: Optional[str] = None,
    modifier3: Optional[str] = None,
    modifier4: Optional[str] = None,
    is_repair: bool = False,
    is_replacement: bool = False
) -> Tuple[Decimal, str]:
    """
    Calculate the invoice modifier and reason based on billing parameters.
    
    Args:
        sale_rent_type (str): Type of sale/rental ('Sale', 'Rental', 'Capped Rental')
        billing_month (int): Current billing month
        dos_from (datetime): Start date of service
        dos_to (datetime): End date of service
        end_date (Optional[datetime]): Final end date of service
        modifier1 (Optional[str]): First modifier code
        modifier2 (Optional[str]): Second modifier code
        modifier3 (Optional[str]): Third modifier code
        modifier4 (Optional[str]): Fourth modifier code
        is_repair (bool): Whether this is a repair
        is_replacement (bool): Whether this is a replacement
        
    Returns:
        Tuple[Decimal, str]: (Modifier amount, Reason for modification)
    """
    # For sales, no modifier applies
    if sale_rent_type == 'Sale':
        return Decimal('1.0'), 'Standard sale pricing'
        
    # Get all applicable modifiers
    modifiers = [m for m in [modifier1, modifier2, modifier3, modifier4] if m]
    
    # Handle repairs and replacements
    if is_repair:
        return Decimal('0.0'), 'No charge for repair'
    if is_replacement:
        return Decimal('0.0'), 'No charge for replacement'
        
    # Check for special modifiers
    if 'RR' in modifiers:  # Rental Replacement
        return Decimal('0.0'), 'No charge for rental replacement'
        
    # Handle capped rentals
    if sale_rent_type == 'Capped Rental':
        if billing_month > 13:  # After 13 months, capped rentals are free
            return Decimal('0.0'), 'Capped rental exceeded 13 months'
        if billing_month > 10:  # Reduced rate after 10 months
            return Decimal('0.75'), 'Capped rental months 11-13'
            
    # Handle regular rentals
    if sale_rent_type == 'Rental':
        # New equipment (NU modifier)
        if 'NU' in modifiers:
            if billing_month == 1:
                return Decimal('1.0'), 'New equipment first month'
            elif billing_month <= 3:
                return Decimal('0.75'), 'New equipment months 2-3'
            else:
                return Decimal('0.5'), 'New equipment after month 3'
                
        # Used equipment (UE modifier)
        if 'UE' in modifiers:
            if billing_month == 1:
                return Decimal('0.75'), 'Used equipment first month'
            else:
                return Decimal('0.5'), 'Used equipment after month 1'
                
    # Check if we're in a partial month
    if end_date and dos_to > end_date:
        days_in_period = (end_date - dos_from).days + 1
        total_days = (dos_to - dos_from).days + 1
        if days_in_period < total_days:
            modifier = Decimal(days_in_period) / Decimal(total_days)
            return modifier, f'Partial month: {days_in_period}/{total_days} days'
            
    # Default case - no modification
    return Decimal('1.0'), 'Standard rental pricing'
