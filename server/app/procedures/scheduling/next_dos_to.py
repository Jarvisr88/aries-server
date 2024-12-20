"""
Function to calculate the end date of service (DOS To) based on billing parameters.

This function determines the appropriate end date for a service period based on
the start date, billing frequency, and other parameters.
"""
from datetime import datetime, timedelta
from typing import Optional
from calendar import monthrange

def get_next_dos_to(
    dos_from: datetime,
    sale_rent_type: str,
    billing_month: int,
    billed_when: str,
    frequency: Optional[str] = None,
    frequency_days: Optional[int] = None,
    end_date: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Calculate the end date of service based on billing parameters.
    
    Args:
        dos_from (datetime): Starting date of service
        sale_rent_type (str): Type of sale/rental ('Sale', 'Rental', 'Capped Rental')
        billing_month (int): Current billing month
        billed_when (str): Billing frequency ('One Time', 'Monthly', 'Weekly', etc.)
        frequency (Optional[str]): Custom frequency pattern (e.g., 'Every 2 Weeks')
        frequency_days (Optional[int]): Number of days in custom frequency
        end_date (Optional[datetime]): Final end date of service
        
    Returns:
        Optional[datetime]: Calculated end date of service, or None if invalid parameters
    """
    if not dos_from:
        return None
        
    # For sales, DOS To is same as DOS From
    if sale_rent_type == 'Sale':
        return dos_from
        
    # If we have an end date and we're past it, use the end date
    if end_date and dos_from > end_date:
        return end_date
        
    # Handle different billing frequencies
    if billed_when == 'One Time':
        return dos_from
        
    elif billed_when == 'Monthly':
        # Calculate last day of the month
        _, last_day = monthrange(dos_from.year, dos_from.month)
        next_dos_to = datetime(dos_from.year, dos_from.month, last_day)
        
        # For rentals after first month, calculate based on billing month
        if sale_rent_type in ('Rental', 'Capped Rental') and billing_month > 1:
            for _ in range(billing_month - 1):
                if next_dos_to.month == 12:
                    next_year = next_dos_to.year + 1
                    next_month = 1
                else:
                    next_year = next_dos_to.year
                    next_month = next_dos_to.month + 1
                _, last_day = monthrange(next_year, next_month)
                next_dos_to = datetime(next_year, next_month, last_day)
                
    elif billed_when == 'Weekly':
        next_dos_to = dos_from + timedelta(days=6)  # 7 days inclusive of start date
        
    elif billed_when == 'Bi-Weekly':
        next_dos_to = dos_from + timedelta(days=13)  # 14 days inclusive of start date
        
    elif frequency and frequency_days:
        next_dos_to = dos_from + timedelta(days=frequency_days - 1)
        
    else:
        return None
        
    # If we have an end date, don't go past it
    if end_date and next_dos_to > end_date:
        return end_date
        
    return next_dos_to
