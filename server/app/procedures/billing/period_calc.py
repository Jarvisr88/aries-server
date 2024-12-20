from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

class BillingFrequency(str, Enum):
    """Billing frequency types"""
    DAILY = 'Daily'
    WEEKLY = 'Weekly'
    BIWEEKLY = 'Bi-Weekly'
    MONTHLY = 'Monthly'
    BIMONTHLY = 'Bi-Monthly'
    QUARTERLY = 'Quarterly'
    SEMIANNUAL = 'Semi-Annual'
    ANNUAL = 'Annual'

class PeriodCalculator:
    """Calculates billing periods based on dates and frequencies"""

    @staticmethod
    def get_period_end(from_date: datetime,
                      to_date: Optional[datetime],
                      frequency: str) -> datetime:
        """
        Calculate the period end date based on frequency
        
        Args:
            from_date: Start date of the period
            to_date: End date constraint (optional)
            frequency: Billing frequency
            
        Returns:
            Calculated period end date
        """
        if not isinstance(frequency, BillingFrequency):
            try:
                frequency = BillingFrequency(frequency)
            except ValueError:
                frequency = BillingFrequency.MONTHLY

        # Calculate period end based on frequency
        if frequency == BillingFrequency.DAILY:
            period_end = from_date + timedelta(days=1)
        elif frequency == BillingFrequency.WEEKLY:
            period_end = from_date + timedelta(weeks=1)
        elif frequency == BillingFrequency.BIWEEKLY:
            period_end = from_date + timedelta(weeks=2)
        elif frequency == BillingFrequency.MONTHLY:
            # Add one month
            year = from_date.year + ((from_date.month + 1) // 12)
            month = ((from_date.month + 1) % 12) or 12
            day = min(from_date.day, [31,29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
            period_end = datetime(year, month, day)
        elif frequency == BillingFrequency.BIMONTHLY:
            # Add two months
            year = from_date.year + ((from_date.month + 2) // 12)
            month = ((from_date.month + 2) % 12) or 12
            day = min(from_date.day, [31,29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
            period_end = datetime(year, month, day)
        elif frequency == BillingFrequency.QUARTERLY:
            # Add three months
            year = from_date.year + ((from_date.month + 3) // 12)
            month = ((from_date.month + 3) % 12) or 12
            day = min(from_date.day, [31,29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
            period_end = datetime(year, month, day)
        elif frequency == BillingFrequency.SEMIANNUAL:
            # Add six months
            year = from_date.year + ((from_date.month + 6) // 12)
            month = ((from_date.month + 6) % 12) or 12
            day = min(from_date.day, [31,29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
            period_end = datetime(year, month, day)
        elif frequency == BillingFrequency.ANNUAL:
            # Add one year
            year = from_date.year + 1
            month = from_date.month
            day = min(from_date.day, [31,29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
            period_end = datetime(year, month, day)
        else:
            # Default to monthly
            year = from_date.year + ((from_date.month + 1) // 12)
            month = ((from_date.month + 1) % 12) or 12
            day = min(from_date.day, [31,29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
            period_end = datetime(year, month, day)

        # Constrain to to_date if provided
        if to_date and period_end > to_date:
            return to_date

        return period_end

    @staticmethod
    def get_period_end2(from_date: datetime,
                       to_date: Optional[datetime],
                       pickup_date: Optional[datetime],
                       frequency: str) -> datetime:
        """
        Calculate period end considering pickup date
        
        Args:
            from_date: Start date of the period
            to_date: End date constraint (optional)
            pickup_date: Pickup date (optional)
            frequency: Billing frequency
            
        Returns:
            Calculated period end date
        """
        # Get base period end
        period_end = PeriodCalculator.get_period_end(from_date, to_date, frequency)
        
        # Apply pickup date rules
        if not pickup_date:
            return period_end
        elif period_end <= pickup_date:
            return period_end
        elif from_date <= pickup_date:
            return pickup_date
            
        return from_date
