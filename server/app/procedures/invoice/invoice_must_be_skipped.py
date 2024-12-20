"""
Function to determine if an invoice line item should be skipped during invoice generation.

This function evaluates various conditions to determine if an invoice line item should be skipped
based on delivery date, date of service, sale/rent type, billing month, and modifiers.
"""
from datetime import datetime
from typing import Optional

def invoice_must_be_skipped(
    delivery_date: Optional[datetime],
    dos_from: datetime,
    actual_sale_rent_type: str,
    billing_month: int,
    modifier1: Optional[str] = None,
    modifier2: Optional[str] = None,
    modifier3: Optional[str] = None,
    modifier4: Optional[str] = None,
    is_active: bool = True,
    is_completed: bool = False,
    payment_amount: float = 0.0,
    total_amount: float = 0.0
) -> bool:
    """
    Determine if an invoice line item should be skipped during invoice generation.
    
    Args:
        delivery_date (Optional[datetime]): The date the order was delivered
        dos_from (datetime): The starting date of service
        actual_sale_rent_type (str): The type of sale/rental (e.g., 'Sale', 'Rental', 'Capped Rental')
        billing_month (int): The billing month number (1 for first month, 2 for second month, etc.)
        modifier1 (Optional[str]): First modifier code
        modifier2 (Optional[str]): Second modifier code
        modifier3 (Optional[str]): Third modifier code
        modifier4 (Optional[str]): Fourth modifier code
        is_active (bool): Whether the line item is active
        is_completed (bool): Whether the line item is completed
        payment_amount (float): Amount already paid
        total_amount (float): Total amount to be paid
        
    Returns:
        bool: True if the invoice should be skipped, False otherwise
    """
    # Skip if line item is not active
    if not is_active:
        return True
        
    # Skip if line item is already completed
    if is_completed:
        return True
        
    # Skip if fully paid
    if payment_amount >= total_amount and total_amount > 0:
        return True
        
    # If there's no delivery date, we can't bill
    if not delivery_date:
        return True
        
    # For sales, we only bill once on the first month
    if actual_sale_rent_type == 'Sale' and billing_month > 1:
        return True
        
    # For rentals, we need a valid billing month
    if actual_sale_rent_type in ('Rental', 'Capped Rental') and billing_month <= 0:
        return True
        
    # Can't bill before delivery date
    if dos_from < delivery_date:
        return True
        
    # Check for specific modifier combinations that indicate skipping
    modifiers = [m for m in [modifier1, modifier2, modifier3, modifier4] if m]
    
    # RR modifier (Rental Replacement) should skip billing
    if 'RR' in modifiers:
        return True
        
    # NU modifier (New Equipment) should only bill on first month
    if 'NU' in modifiers and billing_month > 1:
        return True
        
    # UE modifier (Used Equipment) should only bill on first month
    if 'UE' in modifiers and billing_month > 1:
        return True
        
    # KX modifier (Documentation on File) requires active status
    if 'KX' in modifiers and not is_active:
        return True
        
    # No conditions met to skip billing
    return False
