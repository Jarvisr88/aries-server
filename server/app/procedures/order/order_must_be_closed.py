"""
Function to determine if an order must be closed based on its current state and history.

This function evaluates various conditions to determine if an order should be closed,
such as completed payments, fulfilled quantities, and end dates reached.
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

def order_must_be_closed(
    order_id: int,
    customer_id: int,
    order_date: datetime,
    delivery_date: Optional[datetime],
    end_date: Optional[datetime],
    total_amount: Decimal,
    payment_amount: Decimal,
    ordered_quantity: int,
    fulfilled_quantity: int,
    sale_rent_type: str,
    billing_month: int,
    is_active: bool = True,
    modifiers: Optional[List[str]] = None,
    has_pending_claims: bool = False,
    has_pending_authorizations: bool = False
) -> bool:
    """
    Determine if an order must be closed based on its current state.
    
    Args:
        order_id (int): Unique identifier for the order
        customer_id (int): Customer identifier
        order_date (datetime): Date the order was placed
        delivery_date (Optional[datetime]): Date the order was delivered
        end_date (Optional[datetime]): Final end date for the order
        total_amount (Decimal): Total amount to be paid
        payment_amount (Decimal): Amount already paid
        ordered_quantity (int): Quantity ordered
        fulfilled_quantity (int): Quantity fulfilled
        sale_rent_type (str): Type of sale/rental
        billing_month (int): Current billing month
        is_active (bool): Whether the order is active
        modifiers (Optional[List[str]]): List of modifier codes
        has_pending_claims (bool): Whether there are pending insurance claims
        has_pending_authorizations (bool): Whether there are pending authorizations
        
    Returns:
        bool: True if the order should be closed, False otherwise
    """
    if not is_active:
        return True
        
    # Check if we have all required data
    if not all([order_id, customer_id, order_date]):
        return False
        
    modifiers = modifiers or []
    
    # For sales
    if sale_rent_type == 'Sale':
        # Must be delivered
        if not delivery_date:
            return False
            
        # Must be fully paid (with small tolerance for rounding)
        if total_amount - payment_amount > Decimal('0.01'):
            return False
            
        # Must be fully fulfilled
        if fulfilled_quantity < ordered_quantity:
            return False
            
        # No pending claims or authorizations
        if has_pending_claims or has_pending_authorizations:
            return False
            
        return True
        
    # For rentals
    if sale_rent_type in ('Rental', 'Capped Rental'):
        # Must be delivered
        if not delivery_date:
            return False
            
        # If end date is set and reached
        if end_date and datetime.now() > end_date:
            # Must be fully paid
            if total_amount - payment_amount > Decimal('0.01'):
                return False
                
            # No pending claims or authorizations
            if has_pending_claims or has_pending_authorizations:
                return False
                
            return True
            
        # For capped rentals, close after 13 months
        if sale_rent_type == 'Capped Rental' and billing_month > 13:
            # Must be fully paid
            if total_amount - payment_amount > Decimal('0.01'):
                return False
                
            return True
            
        # Check for rental replacement modifier
        if 'RR' in modifiers:
            return True
            
    # Default case - keep order open
    return False
