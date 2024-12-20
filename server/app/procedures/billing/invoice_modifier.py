"""
Invoice Modifier Function

Python implementation of the GetInvoiceModifier function for
determining billing modifiers based on rental type and billing month.
"""
from datetime import datetime
from typing import Optional
from enum import Enum


class RentalType(str, Enum):
    """Rental type enumeration"""
    CAPPED_RENTAL = 'Capped Rental'
    PARENTAL_CAPPED_RENTAL = 'Parental Capped Rental'


class ModifierIndex(int, Enum):
    """Modifier index enumeration"""
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4


def get_invoice_modifier(
    delivery_date: datetime,
    sale_rent_type: str,
    billing_month: int,
    index: int,
    modifier1: Optional[str] = None,
    modifier2: Optional[str] = None,
    modifier3: Optional[str] = None,
    modifier4: Optional[str] = None
) -> str:
    """
    Get invoice modifier based on rental type and billing month.
    
    Args:
        delivery_date: Date of delivery
        sale_rent_type: Type of sale/rental
        billing_month: Current billing month
        index: Modifier index (1-4)
        modifier1: First modifier
        modifier2: Second modifier
        modifier3: Third modifier
        modifier4: Fourth modifier
        
    Returns:
        Appropriate modifier string
    """
    # Ensure valid billing month
    if billing_month <= 0:
        billing_month = 1

    # Handle capped rentals
    if sale_rent_type in [RentalType.CAPPED_RENTAL, RentalType.PARENTAL_CAPPED_RENTAL]:
        if index == ModifierIndex.FIRST:
            # Maintenance/service after month 22
            if billing_month >= 22 and (billing_month - 22) % 6 == 0:
                return 'MS'
            return 'RR'

        elif index == ModifierIndex.SECOND:
            # Initial setup and recurring rental
            if billing_month == 1:
                return 'KH'
            elif billing_month <= 3:
                return 'KI'
            elif billing_month <= 15:
                return 'KJ'
            elif billing_month >= 22 and (billing_month - 22) % 6 == 0:
                return 'KX' if modifier4 == 'KX' else ''
            return ''

        elif index == ModifierIndex.THIRD:
            # Pre-2006 vs post-2006 rules
            if delivery_date < datetime(2006, 1, 1):
                if billing_month >= 22 and (billing_month - 22) % 6 == 0:
                    return ''
            else:
                if billing_month >= 12:
                    return 'KX'
            return ''

        elif index == ModifierIndex.FOURTH:
            # Pre-2006 vs post-2006 rules
            if delivery_date < datetime(2006, 1, 1):
                if billing_month >= 22 and (billing_month - 22) % 6 == 0:
                    return ''
            else:
                if billing_month >= 12:
                    return ''
            return ''

    # Return standard modifiers for non-capped rentals
    if index == ModifierIndex.FIRST:
        return modifier1 or ''
    elif index == ModifierIndex.SECOND:
        return modifier2 or ''
    elif index == ModifierIndex.THIRD:
        return modifier3 or ''
    elif index == ModifierIndex.FOURTH:
        return modifier4 or ''
    
    return ''
